from __future__ import print_function

import os
import sys
import traceback

import yaml
import yaml.representer

import argparse

from dmoj import judgeenv
from dmoj.executors import get_available, load_executor
from dmoj.executors.mixins import NullStdoutMixin
from dmoj.utils.ansi import ansi_style


def main():
    parser = argparse.ArgumentParser(description='Automatically configures runtimes')
    parser.add_argument('-s', '--silent', action='store_true', help='silent mode')
    silent = parser.parse_args().silent

    result = {}

    if os.name == 'nt':
        judgeenv.load_env(cli=True)
        if not judgeenv.no_ansi_emu:
            try:
                from colorama import init
                init()
            except ImportError:
                pass

    judgeenv.env['runtime'] = {}

    if silent:
        sys.stderr = open(os.devnull, 'w')

    for name in get_available():
        executor = load_executor(name)

        if executor is None or not hasattr(executor, 'Executor'):
            continue

        Executor = executor.Executor
        if silent and not issubclass(Executor, NullStdoutMixin):
            # if you are printing errors into stdout, you may do so in your own blood
            # *cough* Racket *cough*
            Executor = type('Executor', (NullStdoutMixin, Executor), {})

        if hasattr(Executor, 'autoconfig'):
            if not silent:
                print(ansi_style('%-43s%s' % ('Auto-configuring #ansi[%s](|underline):' % name, '')), end=' ')

            try:
                data = Executor.autoconfig()
                config = data[0]
                success = data[1]
                feedback = data[2]
                errors = '' if len(data) < 4 else data[3]
            except Exception:
                if not silent:
                    print(ansi_style('#ansi[Not supported](red|bold)'))
                    traceback.print_exc()
            else:
                if not silent:
                    print(ansi_style(['#ansi[%s](red|bold)', '#ansi[%s](green|bold)'][success] %
                                 (feedback or ['Failed', 'Success'][success])))

                if not success:
                    if not silent:
                        if config:
                            print('  Attempted:')
                            print('   ', yaml.safe_dump(config, default_flow_style=False).rstrip().replace('\n', '\n' + ' ' * 4))

                        if errors:
                            print('  Errors:')
                            print('   ', errors.replace('\n', '\n' + ' ' * 4))


                if success:
                    result.update(config)

    if not silent:
      print()
      print(ansi_style('#ansi[Configuration result](green|bold|underline):'))
    print(yaml.safe_dump({'runtime': result}, default_flow_style=False).rstrip())

if __name__ == '__main__':
    main()
