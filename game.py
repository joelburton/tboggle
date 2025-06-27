import sqlite3
from random import randint
from ctypes import cdll, POINTER, c_int, c_char_p, byref
from enum import Enum
from dice import DiceSet

c_words = cdll.LoadLibrary("./libwords.so")

WORD_SCORES = [0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11]


def read_dawg(path: str) -> None:
    c_words.read_dawg(c_char_p(path.encode("utf8")))

read_dawg("words.dat")
db = sqlite3.connect("all.sqlite3")
GET_WORD_SQL = "SELECT def FROM defs WHERE word = ?"
def get_def(word):
    r = db.execute(GET_WORD_SQL, [word.upper()])
    defn = r.fetchone() 
    return "" if defn is None else defn[0]




class WordList:
    words: set[str]
    longest: int
    score: int

    def __init__(self):
        self.words = set()
        self.longest = 0
        self.score = 0

    def add(self, word: str):
        self.words.add(word)
        self.longest = max(self.longest, len(word))
        self.score += WORD_SCORES[len(word)]


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

    def __init__(
            self,
            dice_set: DiceSet,
            height: int,
            width: int,
            scores=None,
            duration=120):
        if scores is None:
            scores = WORD_SCORES
        self.dice_set = dice_set
        self.height = height
        self.width = width
        self.scores = scores
        self.legal = WordList()
        self.found = WordList()
        self.bad = WordList()
        self.board = []
        self.duration = duration

    def fill_board(
            self,
            min_words: int = 1,
            max_words: int = -1,
            min_score: int = 1,
            max_score: int = -1,
            min_longest: int = 3,
            max_longest: int = -1,
            max_tries: int = 1000,
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

        words_p = c_words.get_words(
            dice_arr_type(*dice_bytes),
            score_arr_type(*self.scores),
            self.width, self.height,
            min_words, max_words,
            min_score, max_score,
            min_longest, max_longest,
            max_tries,
            random_seed,
            byref(tried),
            byref(board_str_b)
        )

        i = 0
        while words_p[i]:
            self.legal.add(words_p[i].decode('utf-8'))
            i += 1

        board_str = board_str_b.value.decode('utf-8')
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



# c_words.free_words.argtypes = [POINTER(c_char_p)]
# c_words.free_words(words_p)
