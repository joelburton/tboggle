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


// Board struct eliminated - all state moved to global variables

// Global variables for current board (not re-entrant, but faster)
static int g_board_width, g_board_height;
static int g_max_x, g_max_y;
static const int *g_score_counts;
static char g_word[MAX_WORD_LEN + 1];  // Global word buffer
static bool g_board_failed;  // Ultra-fast fail-fast flag

// Board state as global variables (eliminates struct and pointer dereferencing)
static char **g_dice_set;
static Dice g_dice;  // Global dice array
static int g_min_words, g_max_words;
static int g_min_score, g_max_score;
static int g_min_longest, g_max_longest;
static int g_min_legal;
static char **g_word_array;
static int g_num_words;
static int g_longest;
static int g_score;

// Delta lookup table for 8 neighbor directions
static const int g_deltas[8][2] = {
    {-1, -1}, {-1, 0}, {-1, 1},  // Top row
    { 0, -1},          { 0, 1},  // Middle row (skip center)
    { 1, -1}, { 1, 0}, { 1, 1}   // Bottom row
};

// Lookup table for special dice characters '0'-'5'
static const char g_special_dice[6][2] = {
    {'_', '_'},  // '0'
    {'Q', 'U'},  // '1' 
    {'I', 'N'},  // '2'
    {'T', 'H'},  // '3'
    {'E', 'R'},  // '4'
    {'H', 'E'}   // '5'
};



/** Shuffle order of dice.
 *
 * Optimized Fisher-Yates shuffle for performance-critical board generation.
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

void make_dice() {
    const int len = g_board_height * g_board_width;
    shuffle_array(g_dice_set, len);

    for (int i = 0; i < len; i++) {
        g_dice[i] = g_dice_set[i][random() % NUM_FACES];
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
        unsigned int i,
        int word_len,
        const int y,
        const int x,
        int_least64_t used)
{
    // Ultra-fast fail-fast check
    if (g_board_failed) return false;
    
    // Use global board dimensions instead of dereferencing
    const int h = g_board_height;
    const int w = g_board_width;

    // If not a legal tile, can't make word here
    // if (y < 0 || y >= h || x < 0 || x >= w) return true;

    // Make a bitmask for this tile position
    const int_least64_t mask = 0x1 << (y * w + x);

    // If we've already used this tile, can't make word here
    if (used & mask) return true;

    // Find the DAWG-node for existing-DAWG-node plus this letter.
    const char sought = g_dice[y * w + x];

    if (sought >= 'A') {
        while (i != 0 && DAWG_LETTER(dawg, i) != sought) i = DAWG_NEXT(dawg, i);

        // There are no words continuing with this letter
        if (i == 0) return true;

        // Either this is a word or the stem of a word. So update our 'word' to
        // include this letter.
        g_word[word_len++] = sought;
    } else {
        // Use lookup table for special dice characters (O(1) vs switch branching)
        const int idx = sought - '0';
        const char t1 = g_special_dice[idx][0];
        const char t2 = g_special_dice[idx][1];

        while (i != 0 && DAWG_LETTER(dawg, i) != t1) i = DAWG_NEXT(dawg, i);

        // There are no words continuing with this letter
        if (i == 0) return true;

        i = DAWG_CHILD(dawg, i);
        while (i != 0 && DAWG_LETTER(dawg, i) != t2) i = DAWG_NEXT(dawg, i);
        if (i == 0) return true;

        // Either this is a word or the stem of a word. So update our 'word' to
        // include this letter.
        g_word[word_len++] = t1;
        g_word[word_len++] = t2;
    }

    // Mark this tile as used
    used |= mask;

    // Add this word to the found-words.
    if (DAWG_EOW(dawg, i) && word_len >= g_min_legal) {
        g_word[word_len] = '\0';

        if (insert(g_word)) {
            g_num_words++;
            if (g_num_words > g_max_words) {
                g_board_failed = true;
                return false;
            }

            g_score += g_score_counts[word_len];
            if (g_score > g_max_score) {
                g_board_failed = true;
                return false;
            }

            if (word_len > g_longest) {
                g_longest = word_len;
                if (g_longest > g_max_longest) {
                    g_board_failed = true;
                    return false;
                }
            }
        }
    }

    // Check every direction H/V/D from here (will also re-check this tile, but
    // the can't-reuse-this-tile rule prevents it from actually succeeding)

    const unsigned int child = DAWG_CHILD(dawg, i);
    for (int d = 0; d < 8; d++) {
        const int ny = y + g_deltas[d][0];
        const int nx = x + g_deltas[d][1];
        if (ny >= 0 && ny <= g_max_y && nx >= 0 && nx <= g_max_x) {
            if (!find_words(child, word_len, ny, nx, used)) return false;
        }
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

bool find_all_words() {
    reset_hash_table();
    g_num_words = 0;
    g_longest = 0;
    g_score = 0;
    g_board_failed = false;  // Reset fail-fast flag

    for (int y = 0; y < g_board_height; y++) {
        for (int x = 0; x < g_board_width; x++) {
            if (!find_words(1, 0, y, x, 0x0)) return false;
        }
    }
    if (g_num_words < g_min_words) return false;
    if (g_score < g_min_score) return false;
    if (g_longest < g_min_longest) return false;
    if (g_longest > g_max_longest) return false;

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
int fill_board(int max_tries){
    int count = 0;
    while (count++ < max_tries) {
        make_dice();
        if (find_all_words()) return count;
    }
    return -1;
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

void bws_btree_to_array() {
    walk();
    g_word_array = tree_words;
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

    // Set up global board state
    g_dice_set = set;
    g_score_counts = score_counts;
    g_board_width = width;
    g_board_height = height;
    g_max_x = width - 1;
    g_max_y = height - 1;
    g_min_words = min_words;
    g_max_words = max_words == -1 ? INT32_MAX : max_words;
    g_min_score = min_score;
    g_max_score = max_score == -1 ? INT32_MAX : max_score;
    g_min_longest = min_longest;
    g_max_longest = max_longest == -1 ? INT32_MAX : max_longest;
    g_min_legal = min_legal;

    int tries = fill_board(max_tries);
    if (tries == -1) return NULL;

    *num_tries = tries;
    g_dice[width * height] = '\0';
    *dice_simple = g_dice;
    bws_btree_to_array();
    g_word_array[g_num_words] = NULL;
    return g_word_array;
}

/** Restore an existing game by passing in the exact dice. */

char **restore_game(
    int score_counts[],
    int width,
    int height,
    Dice dice
) {
    // Set up global board state
    g_score_counts = score_counts;
    g_board_width = width;
    g_board_height = height;
    g_max_x = width - 1;
    g_max_y = height - 1;
    g_min_words = 0;
    g_max_words = INT32_MAX;
    g_min_score = 0;
    g_max_score = INT32_MAX;
    g_min_longest = 0;
    g_max_longest = INT32_MAX;
    g_min_legal = 0;
    strcpy(g_dice, dice);

    find_all_words();
    bws_btree_to_array();
    g_word_array[g_num_words] = NULL;

    return g_word_array;
}
