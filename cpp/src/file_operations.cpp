#include <iostream>
#include <fstream>
#include "C:\Users\HP\Downloads\Telegram Desktop\distributed-file-system\distributed-file-system\cpp\src\file_operations.cpp"


void create_file(const std::string& filename) {
    std::ofstream file(filename);
    if (file) {
        std::cout << "File created: " << filename << std::endl;
    } else {
        std::cerr << "Failed to create file: " << filename << std::endl;
    }
}
