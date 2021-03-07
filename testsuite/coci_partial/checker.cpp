#include <fstream>
#include <iostream>
#include <istream>
#include <memory>
#include <string>

int main(int argc, char *argv[]) {
  std::unique_ptr<std::ifstream> streamPtr =
      std::make_unique<std::ifstream>(std::string(argv[2]));
  std::istream &in = *streamPtr;
  std::string s;
  while (getline(in, s))
    std::cerr << s << std::endl;
  return 7;
}
