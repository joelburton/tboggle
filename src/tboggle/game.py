import sqlite3
import os
import glob
from random import randint
from ctypes import cdll, POINTER, c_int, c_short, c_char_p, byref
from enum import Enum
from collections import Counter

from tboggle.dice import DiceSet


def _find_libwords():
    """Find libwords shared object."""
    module_dir = os.path.dirname(__file__)
    pattern = os.path.join(module_dir, "libwords*.so")
    matches = glob.glob(pattern)
    return matches[0]

c_words = cdll.LoadLibrary(_find_libwords())

def read_dawg(path: str) -> None:
    c_words.read_dawg(c_char_p(path.encode("utf8")))

def _find_data_file(filename):
    """Find data file in package."""
    module_dir = os.path.dirname(__file__)
    package_path = os.path.join(module_dir, filename)

    if os.path.exists(package_path):
        return package_path

    print(f"Warning: using local copy {filename}")
    return filename

read_dawg(_find_data_file("words.dat"))
db = sqlite3.connect(_find_data_file("all.sqlite3"))
GET_WORD_SQL = "SELECT def FROM defs WHERE word = ?"
def get_def(word):
    r = db.execute(GET_WORD_SQL, [word.upper()])
    defn = r.fetchone()
    return "" if defn is None else defn[0]


class WordList:
    words: set[str]
    longest: int
    score: int
    scores: list[int]

    def __init__(self, scores):
        self.words = set()
        self.longest = 0
        self.score = 0
        self.scores = scores

    def add(self, word: str):
        self.words.add(word.lower())
        self.longest = max(self.longest, len(word))
        self.score += self.scores[len(word)]


class GuessResult(Enum):
    GOOD = 0
    BAD = 1
    DUP = 2


class Game:
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
            duration=120,
            min_legal=3,
    ):
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

    def restore_game(self, dice: str):
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
            max_tries: int = 100_000,
            random_seed: int = None,
    ):
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

    def _finish(self, board_str, words):
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

    def handle_guess(self, word):
        if word in self.found.words:
            return GuessResult.DUP
        elif word in self.legal.words:
            self.found.add(word)
            return GuessResult.GOOD
        else:
            self.bad.add(word)
            return GuessResult.BAD

    def get_missed(self):
        return self.legal.words - self.found.words

    def freqs(self):
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

