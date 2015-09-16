import sys


def test_executor(name, Executor, code, problem='self-test', sandbox=True):
    print 'Self-testing: %s executor:' % name,
    try:
        executor = Executor(problem, code)
        proc = executor.launch(time=1, memory=16384) if sandbox else executor.launch_unsafe()
        stdout, stderr = proc.communicate()
        res = stdout.strip() == 'Hello, World!' and not stderr
        print ['Failed', 'Success'][res]
        if not res:
            print>>sys.stdout, stdout
            print>>sys.stderr, stderr
        return res
    except Exception:
        print 'Failed'
        import traceback
        traceback.print_exc()
        return False
