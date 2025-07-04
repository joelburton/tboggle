#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#define HASH_SIZE 7919  // Prime number > 5000
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
    word_list[word_count++] = hash_table[index].word;
    used_indices[used_count++] = index;  // Track this index for reset
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

char **tree_words;
int tree_walk_i;

void walk() {
    tree_walk_i = 0;
    tree_words = word_list;
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

