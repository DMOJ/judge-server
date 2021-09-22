import os
import traceback
from importlib import import_module

import yaml

from dmoj import judgeenv
from dmoj.contrib import load_contrib_modules
from dmoj.executors import executors
from dmoj.testsuite import Tester
from dmoj.utils.ansi import print_ansi


def ci_test(executors_to_test, overrides, allow_fail=frozenset()):
    result = {}
    failed = False
    failed_executors = []

    for name in executors_to_test:
        executor = import_module('dmoj.executors.' + name)

        print_ansi('%-34s%s' % ('Testing #ansi[%s](|underline):' % name, ''), end=' ')

        if not hasattr(executor, 'Executor'):
            failed = True
            print_ansi('#ansi[Does not export](red|bold) #ansi[Executor](red|underline)')
            continue

        if not hasattr(executor.Executor, 'autoconfig'):
            print_ansi('#ansi[Could not autoconfig](magenta|bold)')
            continue

        try:
            if name in overrides:
                if not overrides[name]:
                    print_ansi('#ansi[Environment not found on Travis](red)')
                    continue
                print_ansi('#ansi[(manual config)](yellow)', end=' ')
                data = executor.Executor.autoconfig_run_test(overrides[name])
            else:
                data = executor.Executor.autoconfig()
            config = data[0]
            success = data[1]
            feedback = data[2]
            errors = '' if len(data) < 4 else data[3]
        except Exception:
            print_ansi('#ansi[Autoconfig broken](red|bold)')
            traceback.print_exc()
            if name not in allow_fail:
                failed = True
                failed_executors.append(name)
        else:
            print_ansi(
                ['#ansi[%s](red|bold)', '#ansi[%s](green|bold)'][success] % (feedback or ['Failed', 'Success'][success])
            )

            if success:
                result.update(config)
                executor.Executor.runtime_dict = config
                executors[name] = executor
                for runtime, ver in executor.Executor.get_runtime_versions():
                    print_ansi('  #ansi[%s](cyan): %s' % (runtime, '.'.join(map(str, ver))) if ver else 'unknown')
            else:
                if feedback == 'Could not find JVM':
                    continue

                if config:
                    print('  Attempted:')
                    print(
                        '   ', yaml.safe_dump(config, default_flow_style=False).rstrip().replace('\n', '\n' + ' ' * 4)
                    )

                if errors:
                    print('  Errors:')
                    print('   ', errors.replace('\n', '\n' + ' ' * 4))
                if name not in allow_fail:
                    failed = True
                    failed_executors.append(name)

    print()
    print_ansi('#ansi[Configuration result](green|bold|underline):')
    print(yaml.safe_dump({'runtime': result}, default_flow_style=False).rstrip())
    print()
    if failed:
        print_ansi('#ansi[Executor configuration failed.](red|bold)')
        print_ansi('#ansi[Failed executors:](|bold)', ', '.join(failed_executors))
    else:
        print_ansi('#ansi[Executor configuration succeeded.](green|bold)')
    load_contrib_modules()
    print()
    print()
    print('Running test cases...')
    judgeenv.problem_dirs = [os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'testsuite'))]
    tester = Tester()
    fails = tester.test_all()
    print()
    print('Test complete.')
    if fails:
        print_ansi('#ansi[A total of %d case(s) failed](red|bold).' % fails)
    else:
        print_ansi('#ansi[All cases passed.](green|bold)')
    failed |= fails != 0
    raise SystemExit(int(failed))
