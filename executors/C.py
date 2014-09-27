from .GCCExecutor import make_executor

Executor, initialize = make_executor('C', 'gcc', ['-std=c99'], '.c', '''\
#include <stdio.h>

int main() {
    puts("Hello, World!");
    return 0;
}
''')

del make_executor