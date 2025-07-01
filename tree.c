#include <stdio.h>
#include <stdbool.h>
#include <string.h>

typedef struct sBNode {
    int left;
    int right;
    char word[17];
} BNode;

BNode tree[5001];

// index of last item added to tree
int tree_end = 0;

// node #0 is just a placeholder for an empty tree

/** Check/insert word. Returns true if added, false if found. */

bool insert(char *word) {
    if (tree_end == 0) {
        strcpy(tree[++tree_end].word, word);
        tree[tree_end].left = tree[tree_end].right = 0;
        return true;
    }

    int current = 1;
    while (true) {
        int comp = strcmp(word, tree[current].word);
        if (comp < 0) {
            if (tree[current].left == 0) {
                tree[current].left = ++tree_end;
                strcpy(tree[tree_end].word, word);
                tree[tree_end].left = tree[tree_end].right = 0;
                return true;
            }
            current = tree[current].left;
        } else if (comp > 0) {
            if (tree[current].right == 0) {
                tree[current].right = ++tree_end;
                strcpy(tree[tree_end].word, word);
                tree[tree_end].left = tree[tree_end].right = 0;
                return true;
            }
            current = tree[current].right;
        } else {
            return false;
        }
    }
}

void inorderTraversal(int i) {
    if (i != 0) {
        inorderTraversal(tree[i].left);
        printf("%s\n", tree[i].word);
        inorderTraversal(tree[i].right);
    }
}


void walk() {
    inorderTraversal(1);
}

int main() {
    printf("%d\n", insert("apple"));
    printf("%d\n", insert("berry"));
    printf("%d\n", insert("apple"));
    printf("%d\n", insert("aardvark"));
    printf("%d\n", insert("cherry"));
    walk();

    tree_end = 0;
    insert("moop");
    insert("foo");
    insert("bar");
    walk();
}

