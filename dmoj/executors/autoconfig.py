from collections import OrderedDict

from dmoj.judgeenv import env
from dmoj.executors import get_available, load_executor


def main():
    result = OrderedDict()
    env['runtime'] = {}

    for name in get_available():
        executor = load_executor(name)

        if executor is None or not hasattr(executor, 'Executor'):
            continue

        if hasattr(executor.Executor, 'autoconfig'):
            print 'Auto-configuring %-6s...' % name,
            config = executor.Executor.autoconfig()
            print ['Failed', 'Success'][bool(config)]
            if config:
                result.update(config)

if __name__ == '__main__':
    main()
