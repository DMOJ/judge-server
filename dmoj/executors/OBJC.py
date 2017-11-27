import os

from subprocess import check_output, CalledProcessError
from .gcc_executor import GCCExecutor
from dmoj.judgeenv import env


class Executor(GCCExecutor):
    ext = '.m'
    objc_flags = []
    objc_ldflags = []
    command = 'gobjc'
    name = 'OBJC'
    address_grace = 131072

    test_program = r'''
#import <Foundation/Foundation.h>

int main (int argc, const char * argv[]) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    int ch;
    while ((ch = getchar()) != EOF)
        putchar(ch);
    [pool drain];
    return 0;
}
'''

    def get_flags(self):
        return self.objc_flags + super(Executor, self).get_flags()

    def get_ldflags(self):
        return self.objc_ldflags + super(Executor, self).get_ldflags()

    def get_fs(self):
        return super(Executor, self).get_fs() + ['/proc/\d+/cmdline$']

    @classmethod
    def initialize(cls, sandbox=True):
        if 'gnustep-config' not in env['runtime'] or not os.path.isfile(env['runtime']['gnustep-config']):
            return False
        try:
            cls.objc_flags = check_output([env['runtime']['gnustep-config'], '--objc-flags']).split()
            cls.objc_ldflags = check_output([env['runtime']['gnustep-config'], '--base-libs']).split()
        except CalledProcessError:
            return False
        return super(Executor, cls).initialize(sandbox=sandbox)
