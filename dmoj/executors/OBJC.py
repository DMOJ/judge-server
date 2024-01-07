from subprocess import CalledProcessError, check_output
from typing import List

from dmoj.cptbox.filesystem_policies import ExactFile, FilesystemAccessRule, RecursiveDir
from dmoj.executors.base_executor import AutoConfigOutput, AutoConfigResult
from dmoj.executors.c_like_executor import CLikeExecutor, GCCMixin
from dmoj.utils.unicode import utf8text


class Executor(GCCMixin, CLikeExecutor):
    ext = 'm'
    command = 'gcc'
    address_grace = 131072
    compiler_read_fs: List[FilesystemAccessRule] = [RecursiveDir('~')]

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

    def get_flags(self) -> List[str]:
        return self.runtime_dict['objc_flags'] + super().get_flags()

    def get_ldflags(self) -> List[str]:
        return self.runtime_dict['objc_ldflags'] + super().get_ldflags()

    def get_fs(self) -> List[FilesystemAccessRule]:
        return super().get_fs() + [ExactFile('/proc/self/cmdline')]

    @classmethod
    def autoconfig(cls) -> AutoConfigOutput:
        result: AutoConfigResult = {}

        gcc = cls.find_command_from_list(['gcc'])
        if gcc is None:
            return result, False, 'Failed to find "gcc"', ''
        result[cls.command] = gcc

        gnustep_config = cls.find_command_from_list(['gnustep-config'])
        if gnustep_config is None:
            return result, False, 'Failed to find "gnustep-config"', ''

        try:
            result['objc_flags'] = utf8text(check_output([gnustep_config, '--objc-flags'])).split()
        except CalledProcessError:
            return result, False, 'Failed to run "gnustep-config --objc-flags"', ''

        try:
            result['objc_ldflags'] = utf8text(check_output([gnustep_config, '--base-libs'])).split()
        except CalledProcessError:
            return result, False, 'Failed to run "gnustep-config --base-libs"', ''

        data = cls.autoconfig_run_test(result)
        if data[1]:
            data = data[:2] + (f'Using {gcc}',) + data[3:]
        return data
