void read_dawg(const char *path);

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
    int max_tries
);

int main() {
    read_dawg("words.dat");
    char *set[] = {"CCCCCC", "AAAAAA", "TTTTTT", "SSSSSS"};
    int scores[] = {0, 0, 0, 1, 2};
    get_words(
        set,
        scores,
        2,
        2,
        0,
        -1,
        0,
        -1,
        0,
        -1,
        10000
    );
}