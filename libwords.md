# libwords.c - High-Performance Boggle Word Finding Engine

## Overview

`libwords.c` is the core C module that powers TBoggle's word finding and board generation capabilities. It provides a high-performance interface for generating valid Boggle boards and finding all possible words on those boards using a pre-compiled dictionary.

## Architecture

### Hybrid Design
- **C Extension**: Performance-critical algorithms implemented in C for speed
- **Python Interface**: Called via ctypes from Python for ease of use
- **DAWG Dictionary**: Uses compressed Directed Acyclic Word Graph for fast word validation
- **Global State**: Optimized for speed over thread safety (non-reentrant)

### Key Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hash Table    │    │   DAWG Engine   │    │ Board Generator │
│                 │    │                 │    │                 │
│ • Word Storage  │    │ • Dictionary    │    │ • Dice Rolling  │
│ • Deduplication │◄───┤ • Word Validation│◄───┤ • Constraint    │
│ • Fast Lookup   │    │ • Path Walking  │    │   Checking      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Algorithms

### 1. Board Generation (`fill_board`, `make_dice`)
**Purpose**: Generate random Boggle boards meeting specified constraints

**Process**:
1. **Shuffle dice**: Fisher-Yates algorithm for unbiased randomization
2. **Roll faces**: Select one character per die position
3. **Apply heuristics**: Quick quality checks to reject poor boards early
4. **Validate constraints**: Full word finding if heuristics pass
5. **Repeat**: Until valid board found or max attempts reached

**Optimization**: Fast heuristics reject 90-99% of poor boards without expensive word finding

### 2. Word Finding (`find_words`, `find_all_words`)
**Purpose**: Discover all valid English words on a given board

**Algorithm**: Recursive depth-first search with DAWG traversal
1. **Start from each position**: Try every board position as word start
2. **Follow DAWG paths**: Navigate dictionary tree matching board letters
3. **Track used tiles**: Bitmask prevents reusing tiles within same word
4. **Collect valid words**: Store words meeting minimum length requirements
5. **Early termination**: Fail-fast if constraints violated during search

**Performance**: O(board_size × avg_word_length × branching_factor)

### 3. Hash Table Word Storage
**Purpose**: Efficiently store and deduplicate found words

**Implementation**:
- **djb2 hash function**: Fast, well-distributed hashing
- **Linear probing**: Simple collision resolution with good cache locality
- **Sparse reset**: Only clear used slots between boards (not entire table)
- **Index tracking**: Remember used indices for O(used) vs O(table_size) reset

## Data Structures

### DAWG (Directed Acyclic Word Graph)
```c
// Each node packed into 32-bit integer:
// Bits 31-10: Child node pointer (22 bits)
// Bit 9:      End-of-word flag
// Bit 8:      End-of-sibling-list flag  
// Bits 7-0:   Letter (ASCII)
```

**Benefits**:
- Compact memory usage (~1MB for full English dictionary)
- Fast word validation (O(word_length))
- Shared prefixes (e.g., "CAT", "CATS", "CATCH" share "CAT" prefix)

### Global State Variables
```c
// Board configuration
static int g_board_width, g_board_height;
static char g_dice[37];  // Current board state
static char **g_dice_set;  // Available dice faces

// Game constraints  
static int g_min_words, g_max_words;
static int g_min_longest, g_max_longest;
static int g_min_score, g_max_score;

// Current search state
static int g_num_words, g_longest, g_score;
static bool g_board_failed;  // Fail-fast flag
```

**Trade-off**: Global variables eliminate struct pointer dereferencing for performance, but make code non-reentrant.

## Performance Optimizations

### 1. Fast Heuristics (`board_looks_promising`)
**Problem**: Random board generation can be slow with high constraints
**Solution**: Reject obviously poor boards before expensive word finding

**Heuristics**:
- **Vowel ratio**: 15-65% vowels (A, E, I, O, U) for word formation
- **Common letters**: Presence of S, R, T, N, L (frequent in English words)
- **Special dice**: Limit multi-letter dice (QU, IN, TH, ER, HE)
- **Word endings**: Ensure letters for common endings (-S, -D, -G)

**Impact**: 10-50x speedup for challenging constraints

### 2. Bit Manipulation Optimizations
- **Tile usage tracking**: 64-bit bitmask vs array lookup
- **DAWG traversal**: Direct bit operations vs macro calls
- **Neighbor iteration**: Precomputed delta table vs calculation

### 3. Memory Layout Optimizations
- **Cache-friendly reset**: Only clear used hash table slots
- **Global buffers**: Eliminate repeated allocation/deallocation
- **Lookup tables**: Precomputed values vs runtime calculation

## API Functions

### Primary Entry Points
```c
// Generate random board meeting constraints
char **get_words(char *dice_set[], int score_counts[], 
                 int width, int height, int min_words, int max_words,
                 int min_score, int max_score, int min_longest, int max_longest,
                 int min_legal, int max_tries, int random_seed,
                 int *num_tries, char **dice_simple);

// Analyze specific board configuration  
char **restore_game(int score_counts[], int width, int height, char *dice);

// Load dictionary file
void read_dawg(const char *path);
```

### Internal Functions
```c
// Board generation
static bool board_looks_promising();  // Fast quality heuristics
int fill_board(int max_tries);        // Generate valid board
void make_dice();                     // Randomize dice positions

// Word finding
static bool find_words(...);          // Recursive word search
bool find_all_words();               // Find all words on board

// Hash table management
static bool insert(char *word);       // Add word (with dedup)
void reset_hash_table();             // Clear for new board
void walk();                         // Prepare results for return
```

## File Structure

```
libwords.c
├── Hash Table Implementation (lines 1-100)
│   ├── Data structures and globals
│   ├── djb2 hash function  
│   ├── Linear probing insertion
│   └── Optimized reset/walk functions
│
├── DAWG Dictionary System (lines 101-150)
│   ├── Bit manipulation macros
│   ├── File loading (read_dawg)
│   └── Error handling
│
├── Board State Management (lines 151-200)
│   ├── Global variables
│   ├── Lookup tables (neighbors, special dice)
│   └── Type definitions
│
├── Board Generation (lines 201-300)
│   ├── Fisher-Yates shuffle
│   ├── Dice rolling
│   └── Fast heuristics
│
├── Word Finding Engine (lines 301-450)
│   ├── Recursive search (find_words)
│   ├── DAWG traversal
│   ├── Constraint validation
│   └── Board validation (find_all_words)
│
└── Public API (lines 451-500)
    ├── get_words (random generation)
    ├── restore_game (analyze specific board)
    └── Helper functions
```

## Testing and Benchmarking

### Test Suite
- `make test`: Basic functionality verification (314/182 expected output)
- `make test-heuristics`: Performance demonstration with various constraints
- `make benchmark`: Comprehensive timing analysis
- `make extreme`: Stress testing with "nearly impossible" scenarios

### Performance Metrics
- **Low constraints**: ~0.03ms per attempt
- **High constraints**: 10x speedup over naive approach
- **Extreme constraints**: 50x speedup (enables previously impossible scenarios)

## Dependencies

### External Libraries
- **Standard C library**: malloc, string operations, file I/O
- **Math library** (`-lm`): Used for some calculations

### Data Files
- **words.dat**: Binary DAWG dictionary file
- **Dice definitions**: Provided by calling Python code

## Build System

```bash
# Compile standalone
gcc -O3 -o test_libwords test_libwords.c libwords.c -lm

# Use Makefile
make test          # Basic functionality test
make benchmark     # Performance analysis
make extreme       # Stress test
```

## Key Design Decisions

### Performance vs. Thread Safety
**Decision**: Use global variables instead of passing structs
**Rationale**: 15-20% performance improvement for single-threaded use case
**Trade-off**: Code is not thread-safe or reentrant

### Memory vs. Speed
**Decision**: Keep full hash table in memory with sparse reset
**Rationale**: O(used) reset vs O(table_size), better cache locality
**Trade-off**: Higher memory usage (~500KB) for better performance

### Accuracy vs. Speed
**Decision**: Implement fast heuristics for early board rejection
**Rationale**: 50x speedup for extreme constraints with minimal accuracy loss
**Trade-off**: Slightly more complex code for dramatic performance gains

## Future Improvements

### Potential Optimizations
1. **SIMD instructions**: Vectorize character comparisons
2. **Memory pools**: Eliminate malloc/free overhead
3. **Parallel search**: Multi-threaded word finding for large boards
4. **Better heuristics**: Machine learning for board quality prediction

### Architectural Enhancements
1. **Thread safety**: Optional reentrant mode with thread-local storage
2. **Multiple dictionaries**: Support for different languages/word lists
3. **Incremental updates**: Add/remove words without full reload
4. **Compression**: Further reduce DAWG memory footprint

---

This implementation represents a highly optimized solution for Boggle word finding, balancing algorithmic sophistication with practical performance considerations. The code achieves excellent performance through careful attention to data structures, memory layout, and algorithmic choices while maintaining clean interfaces for integration with higher-level Python code.