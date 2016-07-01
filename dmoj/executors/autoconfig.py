import os
import traceback

import yaml
import yaml.representer

from dmoj.executors import get_available, load_executor
from dmoj.judgeenv import env, load_env
from dmoj.utils.ansi import ansi_style


def main():
    result = {}

    if os.name == 'nt':
        load_env(cli=True)

    env['runtime'] = {}

    for name in get_available():
        executor = load_executor(name)

        if executor is None or not hasattr(executor, 'Executor'):
            continue

        if hasattr(executor.Executor, 'autoconfig'):
            print ansi_style('%-43s%s' % ('Auto-configuring #ansi[%s](|underline):' % name, '')),
            try:
                data = executor.Executor.autoconfig()
                config = data[0]
                success = data[1]
                feedback = data[2]
                errors = '' if len(data) < 4 else data[3]
            except Exception:
                print ansi_style('#ansi[Not supported](red|bold)')
                traceback.print_exc()
            else:
                print ansi_style(['#ansi[%s](red|bold)', '#ansi[%s](green|bold)'][success] %
                                 (feedback or ['Failed', 'Success'][success]))

                if not success:
                    if config:
                        print '  Attempted:'
                        print '   ', yaml.dump(config, default_flow_style=False).rstrip().replace('\n', '\n' + ' ' * 4)

                    if errors:
                        print '  Errors:'
                        print '   ', errors.replace('\n', '\n' + ' ' * 4)

                if success:
                    result.update(config)

    print
    print ansi_style('#ansi[Configuration result](green|bold|underline):')
    print yaml.dump({'runtime': result}, default_flow_style=False).rstrip()

if __name__ == '__main__':
    main()
