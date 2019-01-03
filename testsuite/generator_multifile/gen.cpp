#include "testlib.h"
#include <bits/stdc++.h>

using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    cout << atoi(argv[1]) << " " << atoi(argv[2]) << endl;
    cerr << atoi(argv[1]) + atoi(argv[2]) << endl;
}
