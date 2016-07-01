from collections import OrderedDict

from dmoj.judgeenv import env
from dmoj.executors import get_available, load_executor
from dmoj.utils.ansi import ansi_style


def main():
    result = OrderedDict()
    env['runtime'] = {}

    for name in get_available():
        executor = load_executor(name)

        if executor is None or not hasattr(executor, 'Executor'):
            continue

        if hasattr(executor.Executor, 'autoconfig'):
            print ansi_style('%-43s%s' % ('Self-testing #ansi[%s](|underline):' % name, '')),
            config = executor.Executor.autoconfig()
            print ansi_style(['#ansi[Failed](red|bold)', '#ansi[Success](green|bold)'][bool(config)])
            if config:
                result.update(config)

if __name__ == '__main__':
    main()
