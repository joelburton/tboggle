#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

// Forward declarations for libwords functions
void read_dawg(const char *path);
char **restore_game(int score_counts[], int width, int height, char *dice);
char **get_words(char *set[], int score_counts[], int width, int height,
                 int min_words, int max_words, int min_score, int max_score,
                 int min_longest, int max_longest, int min_legal, int max_tries,
                 int random_seed, int *num_tries, char **dice_simple);

// Dice set for 4x4 Boggle (from DiceSet.get_by_name("4") - exact order from dice.py)
char *dice_4x4[] = {
    "AAEEGN", "ABBJOO", "ACHOPS", "AFFKPS",
    "AOOTTW", "CIMOTU", "DEILRX", "DELRVY",
    "DISTTY", "EEGHNW", "EEINSU", "EHRTVW",
    "EIOSST", "ELRTTY", "HIMNU1", "HLNNRZ"
};

int main() {
    // Read the DAWG dictionary
    read_dawg("src/tboggle/words.dat");
    
    // Scoring system from the Python test
    int scores[] = {0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11};
    
    // Test 1: restore_game with specific dice string
    printf("Test 1: restore_game\n");
    char **words1 = restore_game(scores, 4, 4, "ADYERESTLPNAGIE1");
    
    // Count the words
    int count1 = 0;
    if (words1) {
        while (words1[count1] != NULL) {
            count1++;
        }
    }
    printf("%d\n", count1);
    
    // Test 2: get_words with min_longest=11, random_seed=1
    printf("Test 2: get_words with constraints\n");
    
    // Convert dice strings to char* array
    char *dice_set[16];
    for (int i = 0; i < 16; i++) {
        dice_set[i] = dice_4x4[i];
    }
    
    int num_tries;
    char *dice_simple;
    
    char **words2 = get_words(
        dice_set,           // set
        scores,             // score_counts
        4,                  // width
        4,                  // height
        1,                  // min_words
        -1,                 // max_words
        1,                  // min_score
        -1,                 // max_score
        11,                 // min_longest
        -1,                 // max_longest
        3,                  // min_legal
        100000,             // max_tries
        1,                  // random_seed
        &num_tries,         // num_tries
        &dice_simple        // dice_simple
    );
    
    // Count the words
    int count2 = 0;
    if (words2) {
        while (words2[count2] != NULL) {
            count2++;
        }
    }
    printf("%d\n", count2);
    
    return 0;
}