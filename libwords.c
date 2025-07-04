#include <search.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>

#include "tree.c"

// Forward declaration from tree.c
void reset_hash_table();

#define CHILD_BIT_SHIFT 10
#define EOW_BIT_MASK 0X00000200
#define EOL_BIT_MASK 0X00000100
#define LTR_BIT_MASK 0X000000FF

#define DAWG_LETTER(arr, i) ((arr)[i] & LTR_BIT_MASK)
#define DAWG_EOW(arr, i)    ((arr)[i] & EOW_BIT_MASK)
#define DAWG_NEXT(arr, i)  (((arr)[i] & EOL_BIT_MASK) ? 0 : (i) + 1)
#define DAWG_CHILD(arr, i)  ((arr)[i] >> CHILD_BIT_SHIFT)

#define NUM_FACES 6
#define MAX_WORD_LEN 16
char err_msg[1024];

#define FATAL2(m, m2) { \
sprintf(err_msg, "%s:%i: (%s) %s %s", __FILE__, __LINE__, __FUNCTION__, m, m2); \
perror(err_msg); \
exit(1); \
}

// typedef struct {
//    const char *word;
//} BoardWord;

// Maximum board size is 6x6 -- plus one for '\0' at end
typedef char Dice[37];

// We only read the dawg on startup, and it's shared among all boards.
const int32_t *dawg;

/** Read the dictionary file.
 *
 * Reads DAWG into memory.
 *
 * @param path
 */

void read_dawg(const char *path) {
    FILE *f = fopen(path, "rb");
    int32_t nelems;
    if (fread(&nelems, 4, 1, f) != 1) FATAL2("Cannot get size of", path);
    fseek(f, 0, SEEK_END);
    size_t size = ftell(f);
    fseek(f, 0, SEEK_SET);
    int32_t *f2 = malloc(size);
    if (fread(f2, size, 1, f) != 1) FATAL2("Cannot read dict at", path);
    dawg = f2 + 1;
}


/****************************** BOARD *****************************/


typedef struct Board {
    char **set;
    Dice dice;
    const int *score_counts;
    int width;
    int height;
    int min_words;
    int max_words;
    int min_score;
    int max_score;
    int min_longest;
    int max_longest;
    int min_legal;
    void *legal;
    char **word_array;
    int num_words;
    int longest;
    int score;
    char *dice_simple;
} Board;



/** Shuffle order of dice.
 *
 * A fair shuffle using Fisher-Yates.
 */

static void shuffle_array(char *array[], const int n) {
    for (long i = 0; i < n - 1; i++) {
        const long j = i + random() % (n - i);
        char *temp = array[j];
        array[j] = array[i];
        array[i] = temp;
    }
}

/** Fill dice from set randomly. */

void make_dice(Board *b) {
    const int height = b->height;
    const int width = b->width;
    const int len = b->height * b->width;
    shuffle_array(b->set, len);

    int i = 0;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            if (i == len) return;
            b->dice[i] = b->set[i][random() % NUM_FACES];
            i++;
        }
    }
}

/** Find all words starting from this tile and DAWG-pointer.
 *
 * This is a recursive function -- it is given a tile (via y and x)
 * and a DAWG pointer of where it is in a current word (along with the word
 * and word_len for that word). For example, it might be given the tile at
 * (1,1) and a DAWG-pointer to the end letter of C->A->T. For this example,
 * word="CAT" and word_len=3. It would the note that "CAT" is a good word,
 * and the recurse to all the neighboring tiles.
 *
 * Since you can only use a given tile once per word, it keeps a bitmask of
 * used tile positions. If the tile at the given position is already used,
 * this returns without continuing searching.
 *
 * @param board      Board
 * @param i          Pointer to item in DAWG
 * @param word       Word that we're currently making
 * @param word_len   length of word we're currently making
 * @param y          y pos of tile
 * @param x          x pos of tile
 * @param used       bitmask of tile positions used
 *
 * Returns true/false -- this isn't about "did this find a word?", but about
 *   whether we've violated an invariant (too many words, too high a score,
 *   etc.)
 */

static bool find_words( // NOLINT(*-no-recursion)
        Board *board,
        unsigned int i,
        char *word,
        int word_len,
        const int y,
        const int x,
        int_least64_t used)
{
    const int h = board->height;
    const int w = board->width;

    // If not a legal tile, can't make word here
    // if (y < 0 || y >= h || x < 0 || x >= w) return true;

    // Make a bitmask for this tile position
    const int_least64_t mask = 0x1 << (y * w + x);

    // If we've already used this tile, can't make word here
    if (used & mask) return true;

    // Find the DAWG-node for existing-DAWG-node plus this letter.
    const char sought = board->dice[y * w + x];

    if (sought >= 'A') {
        while (i != 0 && DAWG_LETTER(dawg, i) != sought) i = DAWG_NEXT(dawg, i);

        // There are no words continuing with this letter
        if (i == 0) return true;

        // Either this is a word or the stem of a word. So update our 'word' to
        // include this letter.
        word[word_len++] = sought;
    } else {
        char t1, t2;

        switch (sought) {
            case '0':
                t1 = '_';
                t2 = '_';
                break;
            case '1':
                t1 = 'Q';
                t2 = 'U';
                break;
            case '2':
                t1 = 'I';
                t2 = 'N';
                break;
            case '3':
                t1 = 'T';
                t2 = 'H';
                break;
            case '4':
                t1 = 'E';
                t2 = 'R';
                break;
            case '5':
                t1 = 'H';
                t2 = 'E';
        }

        while (i != 0 && DAWG_LETTER(dawg, i) != t1) i = DAWG_NEXT(dawg, i);

        // There are no words continuing with this letter
        if (i == 0) return true;

        i = DAWG_CHILD(dawg, i);
        while (i != 0 && DAWG_LETTER(dawg, i) != t2) i = DAWG_NEXT(dawg, i);
        if (i == 0) return true;

        // Either this is a word or the stem of a word. So update our 'word' to
        // include this letter.
        word[word_len++] = t1;
        word[word_len++] = t2;
    }

    // Mark this tile as used
    used |= mask;

    // Add this word to the found-words.
    if (DAWG_EOW(dawg, i) && word_len >= board->min_legal) {
        word[word_len] = '\0';

        if (insert(word)) {
            board->num_words++;
            if (board->num_words > board->max_words) return false;

            board->score += board->score_counts[word_len];
            if (board->score > board->max_score) return false;

            if (word_len > board->longest) {
                board->longest = word_len;
                if (board->longest > board->max_longest) return false;
            }
        }
    }

    // Check every direction H/V/D from here (will also re-check this tile, but
    // the can't-reuse-this-tile rule prevents it from actually succeeding)

    const int my = h - 1;
    const int mx = w - 1;
    const unsigned int child = DAWG_CHILD(dawg, i);
    if (y > 0) {
        if (x > 0 && !find_words(board, child, word, word_len, y - 1, x - 1, used)) return false;
        if (!find_words(board, child, word, word_len, y - 1, x, used)) return false;
        if (x < mx && !find_words(board, child, word, word_len, y - 1, x + 1, used)) return false;
    }
    if (x > 0 && !find_words(board, child, word, word_len, y, x - 1, used)) return false;
    if (x < mx && !find_words(board, child, word, word_len, y, x + 1, used)) return false;
    if (y < mx) {
        if (x > 0 && !find_words(board, child, word, word_len, y + 1, x - 1, used)) return false;
        if (!find_words(board, child, word, word_len, y + 1, x, used)) return false;
        if (x < mx && !find_words(board, child, word, word_len, y + 1, x + 1, used)) return false;
    }

    //for (int di = -1; di < 2; di++) {
    //    for (int dj = -1; dj < 2; dj++) {
    //        if (!find_words(
    //            board,
    //            DAWG_CHILD(dawg, i),
    //            word,
    //            word_len,
    //            y + di,
    //            x + dj,
    //            used
    //        )) return false;
    //    }
    //}
    return true;
}


/** Find all words on board.
 *
 * Returns true if this board meets requirements, else false.
 **/

bool find_all_words(Board *b) {
    reset_hash_table();
    b->num_words = 0;
    b->longest = 0;
    b->score = 0;
    b->legal = NULL;

    char word[MAX_WORD_LEN + 1];

    for (int y = 0; y < b->height; y++) {
        for (int x = 0; x < b->width; x++) {
            if (!find_words(b, 1, word, 0, y, x, 0x0)) return false;
        }
    }
    if (b->num_words < b->min_words) return false;
    if (b->score < b->min_score) return false;
    if (b->longest < b->min_longest) return false;

    return true;
}
//
//
///** Free word inside a BoardWord. */
//
//void delNode( const void *nodep, const VISIT value, [[maybe_unused]] int level) {
//    const BoardWord *n = *(const BoardWord **) nodep;
//
//    if (value == leaf || value == endorder) {
//        free((void *) n->word);
//        free((void *) n);
//        free((void *) nodep);
//    }
//}
//
///** Free list of legal words. */
//
//void free_words(const Board *board) {
//    twalk(board->legal, delNode);
//    // board->legal = nullptr;
//}
//
int fill_board(Board *board, int max_tries){
    int count = 0;
    while (count++ < max_tries) {
        make_dice(board);
        if (find_all_words(board)) return count;
    }
    return -1;
        // free_words(board);
}


//struct WalkData {
//    char **words;
//    int marker;
//};

//struct WalkData *walker;
//void btree_callback(const void *n, const VISIT value, int depth) {
//    if (value == leaf || value == postorder) {
//        BoardWord *bw = *(BoardWord **)n;
//        walker->words[walker->marker++] = bw->word;
//    }
//}
//
//void bws_btree_to_array(Board *board) {
//    board->word_array = malloc(((board->num_words + 1) * sizeof(BoardWord*)));
//    struct WalkData w = {board->word_array, 0};
//    walker = &w;
//    twalk(board->legal, btree_callback);
//}

void bws_btree_to_array(Board *board) {
    tree_walk_i = 0;
    tree_words = malloc(((board->num_words + 1) * sizeof(char *)));
    walk();
    board->word_array = tree_words;
}

/** Get words for a board matching these requirements.
 *
 * This is called by Python to "get words from a legal board".
 *
 * Returns:
 * - list of words
 * - num_tries handle points to int of number of tries
 * - dice_simple handle points to string of board
 */

char **get_words(
    char *set[],
    int score_counts[],
    int width,
    int height,
    int min_words,
    int max_words,
    int min_score,
    int max_score,
    int min_longest,
    int max_longest,
    int min_legal,
    int max_tries,
    int random_seed,
    int *num_tries,
    char **dice_simple
) {
    srandom(random_seed);
    if (width * height > 36) FATAL2("Oops", "Board too big");

    Board *b = malloc(sizeof(Board));
    b->set = set;
    b->score_counts = score_counts;
    b->width = width;
    b->height = height;
    b->min_words = min_words;
    b->max_words = max_words == -1 ? INT32_MAX : max_words;
    b->min_score = min_score;
    b->max_score = max_score == -1 ? INT32_MAX : max_score;
    b->min_longest = min_longest;
    b->max_longest = max_longest == -1 ? INT32_MAX : max_longest;
    b->min_legal = min_legal;
    b->score = 0;

    int tries = fill_board(b, max_tries);
    if (tries == -1) return NULL;

    *num_tries = tries;
    b->dice[width * height] = '\0';
    *dice_simple = b->dice;
    bws_btree_to_array(b);
    b->word_array[b->num_words] = NULL;
    return b->word_array;
}

/** Restore an existing game by passing in the exact dice. */

char **restore_game(
    int score_counts[],
    int width,
    int height,
    Dice dice
) {
    Board *b = malloc(sizeof(Board));
    b->score_counts = score_counts;
    b->width = width;
    b->height = height;
    b->min_words = 0;
    b->max_words = INT32_MAX;
    b->min_score = 0;
    b->max_score = INT32_MAX;
    b->min_longest = 0;
    b->max_longest = INT32_MAX;
    b->min_legal = 0;
    b->score = 0;
    strcpy(b->dice, dice);

    find_all_words(b);
    bws_btree_to_array(b);
    b->word_array[b->num_words] = NULL;

    return b->word_array;
}
