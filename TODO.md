- do we need HashEntry struct? could the used array be enough?

- preallocate static array for word list rather than ever malloc'ing

- improve documentation

- should we convert to a python extension rather than ctypes?

- idea: the server backend could be in python and just fork since code is non-reentrant

- implement blank tile ?

- suggest heuristic if min_longest > 11 so we reject boards that aren't close to a 2:3 V:C ratio

- incorporate tree.c into libwords.c


