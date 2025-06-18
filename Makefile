libwords.so: words.c
	gcc -g -fPIC -o libwords.so -shared words.c -D_GNU_SOURCE

ctest: ctest.c libwords.so
	gcc -g -o ctest ctest.c -L. -lwords -Wl,-rpath=.
