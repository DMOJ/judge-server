import os
import traceback


class GeneratorManager(object):
    def __init__(self):
        self._cache = {}

    def get_generator(self, filename, flags):
        from dmoj.executors import executors
        from dmoj.config import InvalidInitException

        filename = os.path.abspath(filename)
        flags = tuple(flags)
        if (filename, flags) in self._cache:
            return self._cache[filename, flags]

        try:
            with open(filename) as file:
                source = file.read()
        except:
            traceback.print_exc()
            raise IOError('could not read generator source')

        def find_cpp():
            for grader in ('CPP11', 'CPP0X', 'CPP'):
                if grader in executors:
                    return grader
            raise InvalidInitException("Can't grade with generator. Why did I get this submission?")

        lookup = {
            '.py': executors.get('PY2', None),
            '.py3': executors.get('PY3', None),
            '.c': executors.get('C', None),
            '.cpp': executors.get(find_cpp(), None),
            '.java': executors.get('JAVA', None),
            '.rb': executors.get('RUBY', None)
        }
        clazz = lookup.get(os.path.splitext(filename)[1], None)
        if not clazz:
            raise IOError('could not identify generator extension')

        executor = clazz.Executor('_generator', source)
        if hasattr(executor, 'flags'):
            executor.flags += flags

        self._cache[filename, flags] = executor
        return executor
