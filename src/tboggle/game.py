import sqlite3
import os
import glob
from random import randint
from ctypes import cdll, POINTER, c_int, c_short, c_char_p, byref
from enum import Enum
from collections import Counter
from typing import Optional

from tboggle.dice import DiceSet


def _find_libwords() -> str:
    """Find libwords shared object.
    
    Returns:
        Path to the libwords shared library file.
        
    Raises:
        FileNotFoundError: If no libwords shared library is found.
    """
    module_dir = os.path.dirname(__file__)
    pattern = os.path.join(module_dir, "libwords*.so")
    matches = glob.glob(pattern)
    
    if not matches:
        raise FileNotFoundError(
            f"No libwords shared library found in {module_dir}. "
            f"Expected files matching pattern: {pattern}"
        )
    
    if len(matches) > 1:
        # Use the first match but warn about multiple files
        print(f"Warning: Multiple libwords libraries found: {matches}. Using: {matches[0]}")
    
    return matches[0]

c_words = cdll.LoadLibrary(_find_libwords())

def read_dawg(path: str) -> None:
    c_words.read_dawg(c_char_p(path.encode("utf8")))

def _find_data_file(filename: str) -> str:
    """Find data file in package.
    
    Args:
        filename: Name of the data file to locate.
        
    Returns:
        Path to the data file, either in package or local directory.
        
    Note:
        Falls back to local directory if file not found in package.
    """
    module_dir = os.path.dirname(__file__)
    package_path = os.path.join(module_dir, filename)

    if os.path.exists(package_path):
        return package_path

    print(f"Warning: using local copy {filename}")
    return filename

read_dawg(_find_data_file("words.dat"))
db = sqlite3.connect(_find_data_file("all.sqlite3"))
GET_WORD_SQL = "SELECT def FROM defs WHERE word = ?"
def get_def(word: str) -> str:
    """Get dictionary definition for a word.
    
    Args:
        word: The word to look up (case insensitive).
        
    Returns:
        Definition string, or empty string if not found.
    """
    r = db.execute(GET_WORD_SQL, [word.upper()])
    defn = r.fetchone()
    return "" if defn is None else defn[0]


class WordList:
    """Container for tracking words and their associated scores.
    
    Attributes:
        words: Set of words found/legal in the game.
        longest: Length of the longest word in the list.
        score: Total score of all words in the list.
        scores: Scoring table indexed by word length.
    """
    words: set[str]
    longest: int
    score: int
    scores: list[int]

    def __init__(self, scores: list[int]) -> None:
        """Initialize empty word list with scoring table.
        
        Args:
            scores: List where scores[i] is points for word of length i.
        """
        self.words = set()
        self.longest = 0
        self.score = 0
        self.scores = scores

    def add(self, word: str) -> None:
        """Add a word to the list and update statistics.
        
        Args:
            word: Word to add (will be normalized to lowercase).
        """
        self.words.add(word.lower())
        self.longest = max(self.longest, len(word))
        self.score += self.scores[len(word)]


class GuessResult(Enum):
    """Result of evaluating a word guess."""
    GOOD = 0        # Valid word found on board
    BAD = 1         # Valid word but not on board  
    DUP = 2         # Word already found
    NOT_ON_BOARD = 3  # Word not in dictionary


class Game:
    """Core Boggle game engine.
    
    Manages board state, word validation, and scoring for a Boggle game.
    Interfaces with C library for high-performance word finding.
    
    Attributes:
        dice_set: The dice configuration used for this game.
        height: Board height in dice.
        width: Board width in dice.
        scores: Point values indexed by word length.
        legal: All valid words that can be found on this board.
        found: Words the player has successfully found.
        bad: Invalid words the player has guessed.
        board: 2D grid of letter faces.
        duration: Game time limit in seconds (0 = no limit).
        min_legal: Minimum word length to be considered valid.
    """
    dice_set: DiceSet
    height: int
    width: int
    scores: list[int]
    legal: WordList
    found: WordList
    bad: WordList
    board: list[list[str]]
    duration: int
    min_legal: int

    def __init__(
            self,
            dice_set: DiceSet,
            height: int,
            width: int,
            scores: list[int],
            duration: int = 120,
            min_legal: int = 3,
    ) -> None:
        """Initialize a new Boggle game.
        
        Args:
            dice_set: Dice configuration to use.
            height: Board height in dice.
            width: Board width in dice.
            scores: Point values where scores[i] = points for i-letter word.
            duration: Game time limit in seconds (0 = no limit).
            min_legal: Minimum word length to be considered valid.
        """
        self.dice_set = dice_set
        self.height = height
        self.width = width
        self.scores = scores
        self.legal = WordList(scores)
        self.found = WordList(scores)
        self.bad = WordList(scores)
        self.board = []
        self.duration = duration
        self.min_legal = min_legal

    def restore_game(self, dice: str) -> None:
        """Restore game from a specific dice configuration.
        
        Args:
            dice: String of dice face characters to restore.
        """
        score_arr_type = c_int * len(self.scores)

        c_words.restore_game.restype = POINTER(c_char_p)

        words_p = c_words.restore_game(
            score_arr_type(*self.scores),
            self.width, self.height,
            c_char_p(dice.encode("UTF8")),
        )

        self._finish(dice, words_p)

    def fill_board(
            self,
            min_words: int = 1,
            max_words: int = -1,
            min_score: int = 1,
            max_score: int = -1,
            min_longest: int = 3,
            max_longest: int = -1,
            max_tries: int = 1_000_000,
            random_seed: Optional[int] = None,
    ) -> None:
        """Generate a random board meeting specified constraints.
        
        Args:
            min_words: Minimum number of valid words required.
            max_words: Maximum number of valid words allowed (-1 = no limit).
            min_score: Minimum total score required.
            max_score: Maximum total score allowed (-1 = no limit).
            min_longest: Minimum length of longest word required.
            max_longest: Maximum length of longest word allowed (-1 = no limit).
            max_tries: Maximum generation attempts before giving up.
            random_seed: RNG seed for reproducible results (None = random).
            
        Raises:
            Exception: If no valid board found within max_tries attempts.
        """
        if random_seed is None:
            random_seed = randint(0, 2 ** 32 - 1)
        dice_bytes = [d.encode('utf8') for d in self.dice_set.dice]
        dice_arr_type = c_char_p * len(dice_bytes)
        score_arr_type = c_int * len(self.scores)

        c_words.get_words.restype = POINTER(c_char_p)
        tried = c_int(0)
        board_str_b = c_char_p()

        import time
        t = time.time()
        words_p = c_words.get_words(
            dice_arr_type(*dice_bytes),
            score_arr_type(*self.scores),
            self.width, self.height,
            min_words, max_words,
            min_score, max_score,
            min_longest, max_longest,
            self.min_legal,
            max_tries,
            random_seed,
            byref(tried),
            byref(board_str_b)
        )
        if (not words_p): raise Exception(f"didn't find: {time.time() - t}")

        self._finish(board_str_b.value.decode('utf-8'), words_p)

    def _finish(self, board_str: str, words) -> None:
        """Finalize board setup after C library processing.
        
        Args:
            board_str: Raw board string from C library.
            words: C array of valid word strings.
        """
        i = 0
        while words[i]:
            self.legal.add(words[i].decode('utf-8'))
            i += 1

        for y in range(self.height):
            row = []
            for x in range(self.width):
                face = board_str[y * self.width + x]
                row.append(self.dice_set.get_face_display(face))
            self.board.append(row)

    def handle_guess(self, word: str) -> GuessResult:
        """Evaluate a player's word guess.
        
        Args:
            word: The word guessed by the player.
            
        Returns:
            Result indicating whether guess was valid, duplicate, etc.
        """
        if word in self.found.words:
            return GuessResult.DUP
        elif word in self.legal.words:
            self.found.add(word)
            return GuessResult.GOOD

        defn = get_def(word)
        if defn:
            return GuessResult.NOT_ON_BOARD
        else:
            self.bad.add(word)
            return GuessResult.BAD

    def get_missed(self) -> set[str]:
        """Get set of valid words not yet found by player.
        
        Returns:
            Set of missed words.
        """
        return self.legal.words - self.found.words

    def freqs(self) -> list[tuple[int, int, int]]:
        """Get word frequency statistics by length.
        
        Returns:
            List of (length, legal_count, found_count) tuples.
        """
        legal = Counter(len(w) for w in self.legal.words)
        found = Counter(len(w) for w in self.found.words)
        both = []

        for k in sorted(legal):
            both.append((k, legal[k], found.get(k, 0)))
        
        return both




# c_words.free_words.argtypes = [POINTER(c_char_p)]
# c_words.free_words(words_p)

if __name__ == "__main__":
    scores=(0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11)
    dice = "ADYERESTLPNAGIE1"
    g = Game(DiceSet.get_by_name("4"), 4, 4, scores)
    g.restore_game(dice)
    print(len(g.legal.words))

    g = Game(DiceSet.get_by_name("4"), 4, 4, scores)
    g.fill_board(min_longest=11, random_seed=1)
    print(len(g.legal.words))
