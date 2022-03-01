import os
from subprocess import CalledProcessError, check_output
from typing import List

from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.judgeenv import env
from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    ext = 'm'
    objc_flags: List[str] = []
    objc_ldflags: List[str] = []
    command = 'gobjc'
    address_grace = 131072

    test_program = r"""
#import <Foundation/Foundation.h>

int main (int argc, const char * argv[]) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    int ch;
    while ((ch = getchar()) != EOF)
        putchar(ch);
    [pool drain];
    return 0;
}
"""

    def get_flags(self):
        return self.objc_flags + super().get_flags()

    def get_ldflags(self):
        return self.objc_ldflags + super().get_ldflags()

    def get_fs(self):
        return super().get_fs() + [ExactFile('/proc/self/cmdline')]

    @classmethod
    def initialize(cls):
        if 'gnustep-config' not in env['runtime'] or not os.path.isfile(env['runtime']['gnustep-config']):
            return False
        try:
            cls.objc_flags = check_output([env['runtime']['gnustep-config'], '--objc-flags']).split()
            cls.objc_ldflags = check_output([env['runtime']['gnustep-config'], '--base-libs']).split()
        except CalledProcessError:
            return False
        return super().initialize()
