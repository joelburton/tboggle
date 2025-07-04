#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>

#define HASH_SIZE 15877  // Prime number ~2x original for lower collision rate
#define MAX_WORD_LEN 16

typedef struct {
    char word[MAX_WORD_LEN + 1];
    bool used;
} HashEntry;

HashEntry hash_table[HASH_SIZE];
char *word_list[5001];  // For iteration
int word_count = 0;
int used_indices[5001];  // Track which hash table indices are used
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
bool insert(char *word) {
    unsigned int index = hash_word(word);
    
    while (hash_table[index].used) {
        if (strcmp(hash_table[index].word, word) == 0) {
            return false;  // Already exists
        }
        index = (index + 1) % HASH_SIZE;
    }
    
    strcpy(hash_table[index].word, word);
    hash_table[index].used = true;
    used_indices[used_count++] = index;  // Track this index for reset
    word_count++;
    return true;
}

// Reset hash table for new board
void reset_hash_table() {
    for (int i = 0; i < used_count; i++) {
        hash_table[used_indices[i]].used = false;
    }
    word_count = 0;
    used_count = 0;
}

char **tree_words = NULL;
int tree_walk_i;
static int tree_words_capacity = 0;

void walk() {
    // Grow buffer if needed
    if (word_count > tree_words_capacity) {
        free(tree_words);  // Safe to call on NULL
        tree_words_capacity = word_count + 1000;  // Add some headroom
        tree_words = malloc(tree_words_capacity * sizeof(char *));
    }
    
    tree_walk_i = 0;
    
    // Extract words from hash table using used_indices
    for (int i = 0; i < used_count; i++) {
        int index = used_indices[i];
        tree_words[tree_walk_i++] = hash_table[index].word;
    }
}

int main() {
    tree_words = malloc(1000);
    printf("%d\n", insert("apple"));
    printf("%d\n", insert("berry"));
    printf("%d\n", insert("apple"));
    printf("%d\n", insert("aardvark"));
    printf("%d\n", insert("cherry"));
    walk();

    reset_hash_table();
    insert("moop");
    insert("foo");
    insert("bar");
    walk();
}

