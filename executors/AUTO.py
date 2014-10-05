from .resource_proxy import ResourceProxy
import CPP11
import PY2

class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code, file_extension='py'):
        super(Executor, self).__init__()
        if file_extension == 'py':
            executor_class = PY2.Executor
        elif file_extension in ['cpp', 'cc', 'cxx']:
            executor_class = CPP11.Executor
        else:
            raise NotImplementedError("unsupported extension: %s" % file_extension)
        self.real_executor = executor_class(problem_id, source_code)

    def launch(self, *args, **kwargs):
        return self.real_executor.launch(*args, **kwargs)

def initialize():
    return True
