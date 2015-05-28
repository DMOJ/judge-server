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
        NSString *hello = @"Hello, World!";
        printf("%s\n", [hello cStringUsingEncoding:NSUTF8StringEncoding]);
        [pool drain];
        return 0;
}
'''

    def get_flags(self):
        return self.objc_flags + super(Executor, self).get_flags()

    def get_ldflags(self):
        return self.objc_ldflags + super(Executor, self).get_ldflags()

    @classmethod
    def initialize(cls):
        if 'gnustep-config' not in env['runtime']:
            return False
        try:
            cls.objc_flags = check_output([env['runtime']['gnustep-config'], '--objc-flags']).split()
            cls.objc_ldflags = check_output([env['runtime']['gnustep-config'], '--base-libs']).split()
        except CalledProcessError as e:
            return False
        return super(Executor).initialize()

initialize = Executor.initialize