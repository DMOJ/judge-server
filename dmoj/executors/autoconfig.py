import argparse
import logging
import os
import sys
import traceback

import yaml
import yaml.representer

from dmoj import judgeenv
from dmoj.executors import get_available, load_executor
from dmoj.executors.mixins import NullStdoutMixin
from dmoj.utils.ansi import print_ansi


def main():
    parser = argparse.ArgumentParser(description='Automatically configures runtimes')
    output_conf = parser.add_mutually_exclusive_group()
    output_conf.add_argument('-s', '--silent', action='store_true', help='silent mode')
    output_conf.add_argument('-V', '--verbose', action='store_true', help='verbose mode')
    args = parser.parse_args()

    if not args.silent:
        logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format='%(message)s')

    result = {}
    judgeenv.env['runtime'] = {}

    if args.silent:
        sys.stderr = open(os.devnull, 'w')

    for name in get_available():
        executor = load_executor(name)

        if executor is None or not hasattr(executor, 'Executor'):
            continue

        Executor = executor.Executor
        if not args.verbose and not issubclass(Executor, NullStdoutMixin):
            # if you are printing errors into stdout, you may do so in your own blood
            # *cough* Racket *cough*
            Executor = type('Executor', (NullStdoutMixin, Executor), {})

        if hasattr(Executor, 'autoconfig'):
            if not args.silent:
                print_ansi('%-43s%s' % ('Auto-configuring #ansi[%s](|underline):' % name, ''), end=' ', file=sys.stderr)
                sys.stdout.flush()

            try:
                data = Executor.autoconfig()
                config = data[0]
                success = data[1]
                feedback = data[2]
                errors = '' if len(data) < 4 else data[3]
            except Exception:
                if not args.silent:
                    print_ansi('#ansi[Not supported](red|bold)', file=sys.stderr)
                    traceback.print_exc()
            else:
                if not args.silent:
                    print_ansi(
                        ['#ansi[%s](red|bold)', '#ansi[%s](green|bold)'][success]
                        % (feedback or ['Failed', 'Success'][success]),
                        file=sys.stderr,
                    )

                if not success and args.verbose:
                    if config:
                        print('  Attempted:', file=sys.stderr)
                        print(
                            '   ',
                            yaml.safe_dump(config, default_flow_style=False).rstrip().replace('\n', '\n' + ' ' * 4),
                            file=sys.stderr,
                        )

                    if errors:
                        print('  Errors:', file=sys.stderr)
                        print('   ', errors.replace('\n', '\n' + ' ' * 4), file=sys.stderr)

                if success:
                    result.update(config)
                    Executor = type('Executor', (executor.Executor,), dict(executor.Executor.__dict__))
                    Executor.runtime_dict = config
                    for runtime, version in Executor.get_runtime_versions():
                        print_ansi(
                            '  #ansi[%s](cyan|bold) %s' % (runtime, '.'.join(map(str, version))), file=sys.stderr
                        )

    if not args.silent and sys.stdout.isatty():
        print(file=sys.stderr)

    if result:
        if not args.silent and sys.stdout.isatty():
            print_ansi('#ansi[Configuration result](green|bold|underline):', file=sys.stderr)
    else:
        print_ansi('#ansi[No runtimes configured.](red|bold)', file=sys.__stderr__)
        if not args.verbose:
            print_ansi(
                'Run #ansi[%s -V](|underline) to see why this is the case.' % (parser.prog,), file=sys.__stderr__
            )

    print(yaml.safe_dump({'runtime': result}, default_flow_style=False).rstrip())


if __name__ == '__main__':
    main()
