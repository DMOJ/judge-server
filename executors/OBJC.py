from GCCExecutor import GCCExecutor
from judgeenv import env
from subprocess import check_output, CalledProcessError


class Executor(GCCExecutor):
    ext = '.m'
    objc_flags = []
    objc_ldflags = []
    command = env['runtime'].get('gobjc')
    name = 'OBJC'

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
        return super(Executor, self).get_fs() + ['/proc/\d+/cmdline', '/usr/lib', '/dev/urandom$']

    @classmethod
    def initialize(cls):
        if 'gnustep-config' not in env['runtime']:
            return False
        try:
            cls.objc_flags = check_output([env['runtime']['gnustep-config'], '--objc-flags']).split()
            cls.objc_ldflags = check_output([env['runtime']['gnustep-config'], '--base-libs']).split()
        except CalledProcessError as e:
            return False
        return super(Executor, cls).initialize()

initialize = Executor.initialize
