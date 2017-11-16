from __future__ import print_function
import os
import traceback
from distutils.version import LooseVersion
from importlib import import_module

import re
import yaml

from dmoj import judgeenv
from dmoj.executors import executors
from dmoj.testsuite import Tester
from dmoj.utils.ansi import ansi_style


def find_directory(parent, expr):
    regex = re.compile(expr)
    dirs = [d for d in os.listdir(parent) if regex.match(d)]
    if not dirs:
        return
    return os.path.join(parent, max(dirs, key=LooseVersion))


def make_override(home, parent, expr):
    directory = find_directory(parent, expr)
    if not directory:
        return
    return {home: directory}


def get_dirs(d):
    try:
        return [item for item in os.listdir(d) if os.path.isdir(os.path.join(d, item))]
    except OSError:
        return []


def ci_test(executors_to_test, overrides):
    result = {}
    failed = False

    for name in executors_to_test:
        executor = import_module('dmoj.executors.' + name)

        print(ansi_style('%-34s%s' % ('Testing #ansi[%s](|underline):' % name, '')), end=' ')

        if not hasattr(executor, 'Executor'):
            failed = True
            print(ansi_style('#ansi[Does not export](red|bold) #ansi[Executor](red|underline)'))
            continue

        if not hasattr(executor.Executor, 'autoconfig'):
            print(ansi_style('#ansi[Could not autoconfig](magenta|bold)'))
            continue

        try:
            if name in overrides:
                if not overrides[name]:
                    print(ansi_style('#ansi[Environment not found on Travis](red)'))
                    continue
                print(ansi_style('#ansi[(manual config)](yellow)'), end=' ')
                data = executor.Executor.autoconfig_run_test(overrides[name])
            else:
                data = executor.Executor.autoconfig()
            config = data[0]
            success = data[1]
            feedback = data[2]
            errors = '' if len(data) < 4 else data[3]
        except Exception:
            failed = True
            print(ansi_style('#ansi[Autoconfig broken](red|bold)'))
            traceback.print_exc()
        else:
            print(ansi_style(['#ansi[%s](red|bold)', '#ansi[%s](green|bold)'][success] %
                             (feedback or ['Failed', 'Success'][success])))

            if success:
                result.update(config)
                executor.Executor.runtime_dict = config
                executors[name] = executor
                for runtime, ver in executor.Executor.get_runtime_versions():
                    print(
                        ansi_style('  #ansi[%s](cyan): %s' % (runtime, '.'.join(map(str, ver)) if ver else 'unknown')))
            else:
                if feedback == 'Could not find JVM':
                    continue

                if config:
                    print('  Attempted:')
                    print('   ', yaml.dump(config, default_flow_style=False).rstrip().replace('\n', '\n' + ' ' * 4))

                if errors:
                    print('  Errors:')
                    print('   ', errors.replace('\n', '\n' + ' ' * 4))
                failed = True

    print()
    print(ansi_style('#ansi[Configuration result](green|bold|underline):'))
    print(yaml.dump({'runtime': result}, default_flow_style=False).rstrip())
    print()
    if failed:
        print(ansi_style('#ansi[Executor configuration failed.](red|bold).'))
    else:
        print(ansi_style('#ansi[Executor configuration succeeded.](green|bold).'))
    print()
    print()
    print('Running test cases...')
    judgeenv.problem_dirs = [os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'testsuite'))]
    tester = Tester()
    fails = tester.test_all()
    print()
    print('Test complete')
    if fails:
        print(ansi_style('#ansi[A total of %d case(s) failed](red|bold).') % fails)
    else:
        print(ansi_style('#ansi[All cases passed.](green|bold)'))
    failed |= fails != 0
    raise SystemExit(int(failed))
