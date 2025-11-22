#ifndef HELLO_H
#define HELLO_H

#include <stdio.h>

// Function declaration
void print_hello(void);

// Inline function example
static inline void print_hello_inline(void) {
    printf("Hello, World!\n");
}

#endif // HELLO_H

