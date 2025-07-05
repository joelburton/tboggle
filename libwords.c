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

/**
 * WORD STORAGE HASH TABLE
 * 
 * Fast O(1) hash table for storing unique words found during board analysis.
 * Uses linear probing to handle collisions and tracks used indices for
 * efficient reset between board generations.
 * 
 * Performance characteristics:
 * - Hash size 15877 (prime) minimizes collisions for typical word sets
 * - Linear probing provides good cache locality
 * - Separate used_indices array enables O(used) reset vs O(table_size)
 */

#define HASH_SIZE 15877      // Prime number to minimize hash collisions
#define MAX_WORDS 5000       // Maximum words we expect to find on any board
#define MAX_WORD_LEN 16      // Longest possible word in Boggle

// Hash table storage: 2D array for direct word storage (no malloc needed)
char hash_table[HASH_SIZE][MAX_WORD_LEN + 1];

// Array of pointers into hash table for iteration (populated by walk())
char *word_list[MAX_WORDS + 1];
int word_count = 0;

// Optimization: track which indices are used for O(used) reset
int used_indices[MAX_WORDS + 1];
int used_count = 0;

/**
 * Hash function: djb2 algorithm
 * 
 * Simple but effective hash function with good distribution properties.
 * Formula: hash = hash * 33 + c (using bit shifts for speed)
 * 
 * @param word The word to hash
 * @return Hash value modulo table size
 */
static inline unsigned int hash_word(const char *word) {
    unsigned int hash = 5381;  // djb2 magic number
    while (*word) {
        hash = ((hash << 5) + hash) + *word++;  // hash * 33 + c
    }
    return hash % HASH_SIZE;
}

/**
 * Insert word into hash table (duplicate detection)
 * 
 * Uses linear probing to handle collisions. Returns false if word already
 * exists (duplicate), true if successfully inserted. Tracks indices for
 * efficient table reset.
 * 
 * @param word Word to insert (must be null-terminated)
 * @return true if word was inserted, false if already exists
 */
static inline bool insert(char *word) {
    unsigned int index = hash_word(word);
    
    // Linear probing: find empty slot or existing word
    while (hash_table[index][0] != '\0') {
        if (strcmp(hash_table[index], word) == 0) {
            return false;  // Word already exists (duplicate)
        }
        index = (index + 1) % HASH_SIZE;  // Linear probe to next slot
    }
    
    // Found empty slot: store word and track index
    strcpy(hash_table[index], word);
    used_indices[used_count++] = index;  // Remember for reset
    word_count++;
    return true;  // Successfully inserted new word
}

/**
 * Reset hash table for new board generation
 * 
 * Optimized reset: only clears slots that were actually used rather than
 * zeroing entire table. Provides O(words_used) vs O(table_size) performance.
 */
void reset_hash_table() {
    const int count = used_count;
    for (int i = 0; i < count; i++) {
        hash_table[used_indices[i]][0] = '\0';  // Mark slot as empty
    }
    word_count = 0;
    used_count = 0;
}

/**
 * Build word array for iteration
 * 
 * Populates word_list array with pointers to all stored words.
 * Called after word finding is complete to prepare results.
 */
void walk() {
    for (int i = 0; i < used_count; i++) {
        int index = used_indices[i];
        word_list[i] = hash_table[index];
    }
}

/**
 * DAWG (Directed Acyclic Word Graph) BIT MANIPULATION
 * 
 * The dictionary is stored as a DAWG where each 32-bit integer encodes:
 * - Bits 31-10: Child node pointer (22 bits = 4M possible nodes)
 * - Bit 9: End-of-word flag (EOW_BIT_MASK)
 * - Bit 8: End-of-list flag (EOL_BIT_MASK) 
 * - Bits 7-0: Letter (LTR_BIT_MASK)
 * 
 * This packed representation enables fast dictionary traversal while
 * maintaining compact memory usage.
 */

#define CHILD_BIT_SHIFT 10       // Child pointer starts at bit 10
#define EOW_BIT_MASK 0X00000200  // Bit 9: End of valid word
#define EOL_BIT_MASK 0X00000100  // Bit 8: End of sibling list
#define LTR_BIT_MASK 0X000000FF  // Bits 7-0: Letter value

// DAWG access macros (kept for compatibility, but optimized code uses direct bit ops)
#define DAWG_LETTER(arr, i) ((arr)[i] & LTR_BIT_MASK)
#define DAWG_EOW(arr, i)    ((arr)[i] & EOW_BIT_MASK)
#define DAWG_NEXT(arr, i)  (((arr)[i] & EOL_BIT_MASK) ? 0 : (i) + 1)
#define DAWG_CHILD(arr, i)  ((arr)[i] >> CHILD_BIT_SHIFT)

#define NUM_FACES 6              // Standard Boggle die has 6 faces
char err_msg[1024];              // Buffer for error messages

/**
 * Fatal error macro with context information
 * 
 * Prints detailed error with file, line, function, and custom messages,
 * then exits. Used for unrecoverable errors like file I/O failures.
 */
#define FATAL2(m, m2) { \
sprintf(err_msg, "%s:%i: (%s) %s %s", __FILE__, __LINE__, __FUNCTION__, m, m2); \
perror(err_msg); \
exit(1); \
}

/**
 * Dice array type definition
 * 
 * Maximum board size is 6x6 = 36 positions, plus null terminator.
 * Each position stores a single character from the corresponding die face.
 */
typedef char Dice[37];

/**
 * Global DAWG dictionary pointer
 * 
 * Loaded once at startup and shared across all board generations.
 * Points to packed 32-bit integer array representing the word graph.
 */
const int32_t *dawg;

/**
 * Load DAWG dictionary from binary file
 * 
 * Reads the pre-compiled DAWG dictionary into memory. The file format is:
 * - First 4 bytes: number of elements (currently unused)
 * - Remaining bytes: packed 32-bit integers representing the DAWG nodes
 * 
 * The DAWG pointer is set to skip the first element (element count),
 * so DAWG node indices start at 1 (index 0 represents "no node").
 * 
 * @param path Path to the binary DAWG file (typically "words.dat")
 */
void read_dawg(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) FATAL2("Cannot open", path);
    
    // Read element count (stored but not currently used)
    int32_t nelems;
    if (fread(&nelems, 4, 1, f) != 1) FATAL2("Cannot get size of", path);
    
    // Get total file size
    fseek(f, 0, SEEK_END);
    size_t size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    // Allocate and read entire file
    int32_t *f2 = malloc(size);
    if (!f2) FATAL2("Cannot allocate memory for", path);
    if (fread(f2, size, 1, f) != 1) FATAL2("Cannot read dict at", path);
    
    // Skip first element (count) - DAWG indices start at 1
    dawg = f2 + 1;
    fclose(f);
}


/**
 * BOARD STATE AND GAME LOGIC
 * 
 * Performance-optimized board representation using global variables instead
 * of struct passing. This eliminates pointer dereferencing overhead and
 * improves cache locality for the performance-critical word-finding recursion.
 * 
 * Note: This makes the code non-reentrant but significantly faster.
 */

// Board dimensions and boundaries
static int g_board_width, g_board_height;  // Current board size (typically 4x4)
static int g_max_x, g_max_y;               // Cached boundary values (width-1, height-1)

// Scoring and word building
static const int *g_score_counts;          // Points per word length (from Python)
static char g_word[MAX_WORD_LEN + 1];      // Buffer for current word being built
static bool g_board_failed;                // Ultra-fast fail-fast flag for constraints

// Dice and board configuration  
static char **g_dice_set;                  // Array of die face strings
static Dice g_dice;                        // Current board: array of selected characters

// Game constraints (set by caller)
static int g_min_words, g_max_words;       // Word count constraints
static int g_min_score, g_max_score;       // Score constraints
static int g_min_longest, g_max_longest;   // Longest word constraints
static int g_min_legal;                    // Minimum word length to count

// Current game state (updated during word finding)
static char **g_word_array;                // Result: array of found words
static int g_num_words;                    // Count of words found
static int g_longest;                      // Length of longest word found
static int g_score;                        // Total score of found words

/**
 * Neighbor direction lookup table
 * 
 * Pre-computed deltas for the 8 adjacent positions in a 2D grid.
 * Used for efficient neighbor traversal during recursive word search.
 * Order: NW, N, NE, W, E, SW, S, SE (skipping center)
 */
static const int g_deltas[8][2] = {
    {-1, -1}, {-1, 0}, {-1, 1},  // Top row: NW, N, NE
    { 0, -1},          { 0, 1},  // Middle row: W, E (skip center)
    { 1, -1}, { 1, 0}, { 1, 1}   // Bottom row: SW, S, SE
};

/**
 * Special dice character lookup table
 * 
 * Maps single-character codes to two-letter combinations for special dice.
 * This avoids switch statements and provides O(1) lookup.
 * 
 * Mapping:
 * '0' -> "__" (blank/unused)
 * '1' -> "QU" (Q is always followed by U in English)
 * '2' -> "IN" 
 * '3' -> "TH"
 * '4' -> "ER"
 * '5' -> "HE"
 */
static const char g_special_dice[6][2] = {
    {'_', '_'},  // '0': Placeholder for unused
    {'Q', 'U'},  // '1': QU combination
    {'I', 'N'},  // '2': IN combination
    {'T', 'H'},  // '3': TH combination
    {'E', 'R'},  // '4': ER combination
    {'H', 'E'}   // '5': HE combination
};



/**
 * Fisher-Yates shuffle for random dice arrangement
 * 
 * Performs an unbiased shuffle of the dice array to ensure random board
 * generation. Optimized for small arrays typical in Boggle (16-36 dice).
 * 
 * Algorithm: For each position i, swap with a random position j where j >= i.
 * This ensures each permutation has equal probability.
 * 
 * @param array Array of string pointers to shuffle
 * @param n Number of elements in array
 */
static void shuffle_array(char *array[], const int n) {
    // Optimized for small arrays (most Boggle games are 4x4=16 or 5x5=25)
    for (int i = 0; i < n - 1; i++) {
        const int range = n - i;                   // Remaining elements to choose from
        const int j = i + (random() % range);     // Random position from i to end
        
        // Swap elements at positions i and j
        char *temp = array[j];
        array[j] = array[i];
        array[i] = temp;
    }
}

/**
 * Generate random board configuration
 * 
 * Creates a random board by:
 * 1. Shuffling the dice array to randomize positions
 * 2. Rolling each die to select one of its 6 faces
 * 
 * The result is stored in the global g_dice array as a string of characters.
 */
void make_dice() {
    const int len = g_board_height * g_board_width;
    
    // Randomize which die goes in each position
    shuffle_array(g_dice_set, len);

    // Roll each die to select a face
    for (int i = 0; i < len; i++) {
        g_dice[i] = g_dice_set[i][random() % NUM_FACES];
    }
}

/**
 * Recursive word finder with DAWG traversal and constraint checking
 * 
 * Core algorithm for finding all valid words on the board. Uses depth-first
 * search with backtracking, following paths through the DAWG dictionary.
 * 
 * ALGORITHM:
 * 1. Check if current tile can extend the current word path
 * 2. Navigate DAWG to find if this letter/sequence is valid
 * 3. If we've formed a complete word, add it and check constraints
 * 4. Recursively explore all 8 neighboring tiles
 * 5. Use fail-fast optimization: return immediately if constraints violated
 * 
 * OPTIMIZATION FEATURES:
 * - Bitmask for O(1) used-tile checking instead of array searches
 * - Global variables eliminate struct pointer dereferencing
 * - Direct bit manipulation for DAWG traversal
 * - Fail-fast flag prevents deep recursion after constraint violation
 * - Special dice lookup table for O(1) character expansion
 * 
 * @param i DAWG node index (current position in dictionary tree)
 * @param word_len Current length of word being built
 * @param y Row position of current tile (0-based)
 * @param x Column position of current tile (0-based)  
 * @param used Bitmask of already-used tile positions
 * 
 * @return true if search should continue, false if constraints violated
 *         (NOTE: false doesn't mean "no word found", it means "stop searching")
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
    
    // Cache board dimensions in local variables for better register allocation
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
        // Cache dawg array access
        const int32_t *dawg_ptr = dawg;
        while (i != 0 && (dawg_ptr[i] & LTR_BIT_MASK) != sought) {
            i = (dawg_ptr[i] & EOL_BIT_MASK) ? 0 : i + 1;
        }

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

        // Cache dawg array access
        const int32_t *dawg_ptr = dawg;
        while (i != 0 && (dawg_ptr[i] & LTR_BIT_MASK) != t1) {
            i = (dawg_ptr[i] & EOL_BIT_MASK) ? 0 : i + 1;
        }

        // There are no words continuing with this letter
        if (i == 0) return true;

        i = dawg_ptr[i] >> CHILD_BIT_SHIFT;
        while (i != 0 && (dawg_ptr[i] & LTR_BIT_MASK) != t2) {
            i = (dawg_ptr[i] & EOL_BIT_MASK) ? 0 : i + 1;
        }
        if (i == 0) return true;

        // Either this is a word or the stem of a word. So update our 'word' to
        // include this letter.
        g_word[word_len++] = t1;
        g_word[word_len++] = t2;
    }

    // Mark this tile as used
    used |= mask;

    // Add this word to the found-words.
    if ((dawg[i] & EOW_BIT_MASK) && word_len >= g_min_legal) {
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

    const unsigned int child = dawg[i] >> CHILD_BIT_SHIFT;
    for (int d = 0; d < 8; d++) {
        const int ny = y + g_deltas[d][0];
        const int nx = x + g_deltas[d][1];
        if (ny >= 0 && ny <= g_max_y && nx >= 0 && nx <= g_max_x) {
            if (!find_words(child, word_len, ny, nx, used)) return false;
        }
    }

    return true;
}


/**
 * Find all valid words on the current board
 * 
 * Entry point for word finding. Initiates recursive search from every
 * position on the board and validates final results against constraints.
 * 
 * PROCESS:
 * 1. Reset hash table and counters for new search
 * 2. Try starting a word from each board position
 * 3. find_words() recursively explores all possible paths
 * 4. Check final board statistics against min/max constraints
 * 
 * @return true if board meets all word/score/length requirements, false otherwise
 */
bool find_all_words() {
    // Initialize for new word search
    reset_hash_table();
    g_num_words = 0;
    g_longest = 0;
    g_score = 0;
    g_board_failed = false;  // Reset fail-fast optimization flag

    // Try starting words from every position on the board
    for (int y = 0; y < g_board_height; y++) {
        for (int x = 0; x < g_board_width; x++) {
            // Start with DAWG root (index 1), empty word, no tiles used
            if (!find_words(1, 0, y, x, 0x0)) {
                return false;  // Constraint violation during search
            }
        }
    }
    
    // Validate final results against all constraints
    if (g_num_words < g_min_words) return false;
    if (g_score < g_min_score) return false;
    if (g_longest < g_min_longest) return false;
    if (g_longest > g_max_longest) return false;

    return true;  // Board meets all requirements
}

/**
 * Fast heuristic: check board quality before expensive word finding
 * 
 * Performs quick checks to identify boards that are unlikely to have
 * many words, avoiding the expensive recursive word-finding algorithm.
 * 
 * HEURISTICS CHECKED:
 * 1. Vowel/consonant ratio (target: 30-40% vowels)
 * 2. Common letter presence (S, R, T, N, L are word-builders)
 * 3. Letter distribution (avoid clustering)
 * 4. Special patterns (QU positioning, common endings)
 * 
 * @return true if board looks promising, false if likely poor
 */
static bool board_looks_promising() {
    const int board_size = g_board_width * g_board_height;
    int vowel_count = 0;
    int common_letters = 0;  // Count of S, R, T, N, L
    int special_chars = 0;   // Count of multi-letter dice (1-5)
    
    // Character frequency analysis
    for (int i = 0; i < board_size; i++) {
        char c = g_dice[i];
        
        // Count vowels (including special patterns)
        if (c == 'A' || c == 'E' || c == 'I' || c == 'O' || c == 'U') {
            vowel_count++;
        } else if (c == '2') {  // 'IN' pattern has vowel
            vowel_count++;
        } else if (c == '5') {  // 'HE' pattern has vowel  
            vowel_count++;
        }
        
        // Count common word-building letters
        if (c == 'S' || c == 'R' || c == 'T' || c == 'N' || c == 'L') {
            common_letters++;
        }
        
        // Count special multi-letter dice
        if (c >= '1' && c <= '5') {
            special_chars++;
        }
    }
    
    // Heuristic 1: Vowel ratio check (more permissive range)
    int vowel_percentage = (vowel_count * 100) / board_size;
    if (vowel_percentage < 15 || vowel_percentage > 65) {
        return false;  // Only reject extreme cases
    }
    
    // Heuristic 2: Need some common letters for word building (very permissive)
    if (common_letters < 1) {
        return false;  // Only reject if completely missing common letters
    }
    
    // Heuristic 3: Don't have too many special characters (permissive)
    if (special_chars > board_size / 2) {
        return false;  // Allow up to half special chars
    }
    
    // For high word count requirements, be more selective
    if (g_min_words > 100) {
        // Need better vowel ratio for very high word counts
        if (vowel_percentage < 20 || vowel_percentage > 55) {
            return false;
        }
        // Need more common letters
        if (common_letters < 2) {
            return false;
        }
    }
    
    // Additional check for extremely high requirements only
    if (g_min_words > 200 || g_min_longest > 10) {
        // Must have excellent letter distribution
        if (vowel_count < 3 || common_letters < 3) {
            return false;
        }
        
        // Check for presence of word-ending letters
        bool has_s = false, has_d = false, has_g = false;
        for (int i = 0; i < board_size; i++) {
            char c = g_dice[i];
            if (c == 'S') has_s = true;
            if (c == 'D') has_d = true;
            if (c == 'G') has_g = true;
        }
        
        // Need good word-ending options for very long words
        int endings = has_s + has_d + has_g;
        if (endings < 1) {
            return false;
        }
    }
    
    return true;  // Board looks promising
}

/**
 * Generate a valid board within attempt limit
 * 
 * Repeatedly generates random boards until one meets all the specified
 * constraints (word count, score, longest word, etc.) or max attempts reached.
 * 
 * OPTIMIZATION: Uses fast heuristics to reject unpromising boards before
 * running the expensive word-finding algorithm, significantly improving
 * performance when constraints are high.
 * 
 * @param max_tries Maximum number of board generation attempts
 * @return Number of attempts taken (1-based), or -1 if failed
 */
int fill_board(int max_tries) {
    int count = 0;
    while (count++ < max_tries) {
        make_dice();           // Generate random board
        
        // Fast rejection: skip expensive word finding if board looks poor
        if (!board_looks_promising()) {
            continue;          // Try another board without word analysis
        }
        
        if (find_all_words()) { // Expensive check if it meets requirements
            return count;      // Success: return attempt count
        }
    }
    return -1;  // Failed to generate valid board within limit
}

/**
 * Prepare word list for return to caller
 * 
 * Converts internal hash table to simple array format expected by Python.
 * Legacy function name preserved for compatibility.
 */
void bws_btree_to_array() {
    walk();                    // Populate word_list from hash table
    g_word_array = word_list;  // Set global pointer for return
}

/**
 * Generate a random board meeting specified constraints
 * 
 * Primary entry point called by Python via ctypes. Generates random boards
 * until one meets all the specified requirements or max_tries is exceeded.
 * 
 * CONSTRAINT SYSTEM:
 * - Word count: min_words <= found_words <= max_words
 * - Score: min_score <= total_score <= max_score  
 * - Longest word: min_longest <= longest_word <= max_longest
 * - Word length: only words >= min_legal characters count
 * 
 * @param set Array of dice face strings (one per board position)
 * @param score_counts Points awarded per word length [0]=0pts, [3]=1pt, etc.
 * @param width Board width (typically 4)
 * @param height Board height (typically 4)
 * @param min_words Minimum number of words required
 * @param max_words Maximum words allowed (-1 for unlimited)
 * @param min_score Minimum total score required
 * @param max_score Maximum score allowed (-1 for unlimited)
 * @param min_longest Minimum length of longest word
 * @param max_longest Maximum length of longest word (-1 for unlimited)
 * @param min_legal Minimum word length to count (typically 3)
 * @param max_tries Maximum board generation attempts
 * @param random_seed Seed for reproducible random generation
 * @param[out] num_tries Returns number of attempts taken
 * @param[out] dice_simple Returns final board as string
 * 
 * @return Array of found words (NULL-terminated), or NULL if failed
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

/**
 * Analyze a specific board configuration
 * 
 * Given an exact dice configuration, finds all valid words without any
 * constraints. Used to restore a previous game or analyze a known board.
 * 
 * Unlike get_words(), this doesn't generate random boards - it analyzes
 * the specific board provided in the dice parameter.
 * 
 * @param score_counts Points per word length (for scoring found words)
 * @param width Board width
 * @param height Board height  
 * @param dice Exact board configuration as string (e.g., "ABCD...")
 * 
 * @return Array of all found words (NULL-terminated)
 */

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
