libwords.so: words.c
	gcc -g -fPIC -o libwords.so -shared words.c -D_GNU_SOURCE
