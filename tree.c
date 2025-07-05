#include <stdbool.h>
#include <string.h>
#include <stdlib.h>

#define HASH_SIZE 15877
#define MAX_WORD_LEN 16
#define MAX_WORDS 5000

typedef struct {
    char word[MAX_WORD_LEN + 1];
} HashEntry;

HashEntry hash_table[HASH_SIZE];
char *word_list[MAX_WORDS + 1];  // For iteration
int word_count = 0;
int used_indices[MAX_WORDS + 1];  // Track which hash table indices are used
int used_count = 0;

// Simple hash function (djb2)
static inline unsigned int hash_word(const char *word) {
    unsigned int hash = 5381;
    while (*word) {
        hash = ((hash << 5) + hash) + *word++;
    }
    return hash % HASH_SIZE;
}

/** Check/insert word. Returns true if added, false if found. */
static inline bool insert(char *word) {
    unsigned int index = hash_word(word);
    
    // Check if slot is occupied (non-empty word)
    while (hash_table[index].word[0] != '\0') {
        if (strcmp(hash_table[index].word, word) == 0) {
            return false;  // Already exists
        }
        index = (index + 1) % HASH_SIZE;
    }
    
    strcpy(hash_table[index].word, word);
    used_indices[used_count++] = index;  // Track this index for reset
    word_count++;
    return true;
}

// Reset hash table for new board - optimized for cache efficiency
void reset_hash_table() {
    const int count = used_count;
    for (int i = 0; i < count; i++) {
        hash_table[used_indices[i]].word[0] = '\0';  // Mark as empty
    }
    word_count = 0;
    used_count = 0;
}

void walk() {
    for (int i = 0; i < used_count; i++) {
        int index = used_indices[i];
        word_list[i] = hash_table[index].word;
    }
}

