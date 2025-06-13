from ctypes import cdll, POINTER, c_int, c_char_p, byref

from dice import DiceSet
from random import randint

cwords = cdll.LoadLibrary("./libwords.so")




# if __name__ == "__main__":
#     set = DiceSet.get_by_name("4")
#     words = fill_board(set.dice,WORD_SCORES, 4, 4, min_words=150)
#     print(words)


#