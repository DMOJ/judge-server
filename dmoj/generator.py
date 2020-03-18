import os

from dmoj.utils.helper_files import compile_with_auxiliary_files


class GeneratorManager:
    def get_generator(self, filenames, flags, lang=None, compiler_time_limit=None):
        filenames = list(map(os.path.abspath, filenames))
        return compile_with_auxiliary_files(filenames, lang, compiler_time_limit)
