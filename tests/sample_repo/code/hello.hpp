#ifndef HELLO_HPP
#define HELLO_HPP

#include <iostream>
#include <string>

// Function declaration
void print_hello();

// Class example
class HelloWorld {
public:
    void greet() const;
    void greet(const std::string& name) const;
};

// Inline function example
inline void print_hello_inline() {
    std::cout << "Hello, World!" << std::endl;
}

#endif // HELLO_HPP

