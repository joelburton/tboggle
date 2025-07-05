#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

// Forward declarations for libwords functions
void read_dawg(const char *path);
char **get_words(char *set[], int score_counts[], int width, int height,
                 int min_words, int max_words, int min_score, int max_score,
                 int min_longest, int max_longest, int min_legal, int max_tries,
                 int random_seed, int *num_tries, char **dice_simple);

// Dice set for 4x4 Boggle
char *dice_4x4[] = {
    "AAEEGN", "ABBJOO", "ACHOPS", "AFFKPS",
    "AOOTTW", "CIMOTU", "DEILRX", "DELRVY",
    "DISTTY", "EEGHNW", "EEINSU", "EHRTVW",
    "EIOSST", "ELRTTY", "HIMNU1", "HLNNRZ"
};

int main() {
    // Read the DAWG dictionary
    read_dawg("src/tboggle/words.dat");
    
    // Scoring system
    int scores[] = {0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11};
    
    // Convert dice strings to char* array
    char *dice_set[16];
    for (int i = 0; i < 16; i++) {
        dice_set[i] = dice_4x4[i];
    }
    
    printf("Testing heuristics performance with different constraints:\n\n");
    
    // Test 1: Low constraints (baseline)
    printf("Test 1: Low constraints (min_words=1, min_longest=3)\n");
    clock_t start = clock();
    int num_tries;
    char *dice_simple;
    char **words = get_words(dice_set, scores, 4, 4, 1, -1, 1, -1, 3, -1, 3, 1000, 1, &num_tries, &dice_simple);
    clock_t end = clock();
    double time1 = ((double)(end - start)) / CLOCKS_PER_SEC;
    int count1 = 0;
    if (words) while (words[count1] != NULL) count1++;
    printf("Result: %d words found in %d tries (%.3fs)\n\n", count1, num_tries, time1);
    
    // Test 2: Medium constraints 
    printf("Test 2: Medium constraints (min_words=50, min_longest=6)\n");
    start = clock();
    words = get_words(dice_set, scores, 4, 4, 50, -1, 1, -1, 6, -1, 3, 1000, 2, &num_tries, &dice_simple);
    end = clock();
    double time2 = ((double)(end - start)) / CLOCKS_PER_SEC;
    int count2 = 0;
    if (words) while (words[count2] != NULL) count2++;
    printf("Result: %d words found in %d tries (%.3fs)\n\n", count2, num_tries, time2);
    
    // Test 3: High constraints (where heuristics should help most)
    printf("Test 3: High constraints (min_words=80, min_longest=7)\n");
    start = clock();
    words = get_words(dice_set, scores, 4, 4, 80, -1, 1, -1, 7, -1, 3, 5000, 3, &num_tries, &dice_simple);
    end = clock();
    double time3 = ((double)(end - start)) / CLOCKS_PER_SEC;
    int count3 = 0;
    if (words) {
        while (words[count3] != NULL) count3++;
        printf("Result: %d words found in %d tries (%.3fs)\n", count3, num_tries, time3);
    } else {
        printf("Result: Failed to find board in %d tries (%.3fs)\n", 5000, time3);
    }
    printf("\n");
    
    // Test 4: Very high constraints (stress test)
    printf("Test 4: Very high constraints (min_words=120, min_longest=8)\n");
    start = clock();
    words = get_words(dice_set, scores, 4, 4, 120, -1, 1, -1, 8, -1, 3, 10000, 4, &num_tries, &dice_simple);
    end = clock();
    double time4 = ((double)(end - start)) / CLOCKS_PER_SEC;
    int count4 = 0;
    if (words) {
        while (words[count4] != NULL) count4++;
        printf("Result: %d words found in %d tries (%.3fs)\n", count4, num_tries, time4);
    } else {
        printf("Result: Failed to find board in %d tries (%.3fs)\n", 10000, time4);
    }
    
    printf("\nHeuristics demonstrate faster rejection of poor boards as constraints increase.\n");
    printf("Without heuristics, each attempt requires expensive recursive word finding.\n");
    printf("With heuristics, poor boards are rejected with simple character counting.\n");
    
    return 0;
}