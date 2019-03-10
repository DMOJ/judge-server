from .base_executor import ScriptExecutor

class Executor(ScriptExecutor):
    ext = '.js'
    name = 'MOZJS'
    command_paths = ['js', 'js24', 'js52']
    test_program = 'print(readline());'
    nproc = -1
 
    @classmethod
    def get_version_flags(cls, command):
    	# In js24, there is no version flag, so we must parse the output from the help flag.
        return ['--help'] 
