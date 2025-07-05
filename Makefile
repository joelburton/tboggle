CC = gcc
CFLAGS = -O3 -Wall -Wextra
LIBS = -lm

# Default target
all: test_libwords

# Build the test executable
test_libwords: test_libwords.c libwords.c
	$(CC) $(CFLAGS) -o test_libwords test_libwords.c libwords.c $(LIBS)

# Run the test (depends on building it first)
test: test_libwords
	./test_libwords

# Clean up build artifacts
clean:
	rm -f test_libwords

# Rebuild everything from scratch
rebuild: clean all

.PHONY: all test clean rebuild