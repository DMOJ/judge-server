import sys


def test_executor(name, Executor, code):
    print 'Self-testing: %s executor:' % name,
    try:
        executor = Executor('self-test', code)
        proc = executor.launch(time=1, memory=16384)
        stdout, stderr = proc.communicate()
        res = stdout.strip() == 'Hello, World!' and not stderr
        print ['Failed', 'Success'][res]
        if stderr:
            print>>sys.stderr, stderr
        return res
    except Exception:
        print 'Failed'
        import traceback
        traceback.print_exc()
        return False
