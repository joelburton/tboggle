CC = gcc
CFLAGS = -O3 -Wall -Wextra
LIBS = -lm

# Default target
all: test_libwords

# Build the test executable
test_libwords: test_libwords.c libwords.c
	$(CC) $(CFLAGS) -o test_libwords test_libwords.c libwords.c $(LIBS)

# Build the heuristics performance test
test_heuristics: test_heuristics.c libwords.c
	$(CC) $(CFLAGS) -o test_heuristics test_heuristics.c libwords.c $(LIBS)

# Build the heuristics benchmark
benchmark_heuristics: benchmark_heuristics.c libwords.c
	$(CC) $(CFLAGS) -o benchmark_heuristics benchmark_heuristics.c libwords.c $(LIBS)

# Build the extreme constraints test
test_extreme: test_extreme_constraints.c libwords.c
	$(CC) $(CFLAGS) -o test_extreme test_extreme_constraints.c libwords.c $(LIBS)

# Run the basic test (depends on building it first)
test: test_libwords
	./test_libwords

# Run the heuristics performance test
test-heuristics: test_heuristics
	./test_heuristics

# Run the heuristics benchmark
benchmark: benchmark_heuristics
	./benchmark_heuristics

# Run the extreme constraints test
extreme: test_extreme
	./test_extreme

# Clean up build artifacts
clean:
	rm -f test_libwords test_heuristics benchmark_heuristics test_extreme

# Rebuild everything from scratch
rebuild: clean all

# Rebuild Python C extension (equivalent to old "python setup.py build_ext --inplace")
rebuild-ext:
	pip install -e . --force-reinstall --no-deps

.PHONY: all test test-heuristics benchmark extreme clean rebuild rebuild-ext