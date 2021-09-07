import uuid

from dmoj.error import InternalError
from dmoj.executors import executors
from dmoj.graders.standard import StandardGrader
from dmoj.utils.unicode import utf8bytes


class SignatureGrader(StandardGrader):
    def _generate_binary(self):
        siggraders = ('C', 'C11', 'CPP03', 'CPP11', 'CPP14', 'CPP17', 'CPP20', 'CLANG', 'CLANGX')

        if self.language in siggraders:
            aux_sources = {}
            handler_data = self.problem.config['signature_grader']

            entry_point = self.problem.problem_data[handler_data['entry']]
            header = self.problem.problem_data[handler_data['header']]

            submission_prefix = '#include "%s"\n' % handler_data['header']
            if not handler_data.get('allow_main', False):
                submission_prefix += '#define main main_%s\n' % uuid.uuid4().hex

            aux_sources[self.problem.id + '_submission'] = utf8bytes(submission_prefix) + self.source

            aux_sources[handler_data['header']] = header
            entry = entry_point
            return executors[self.language].Executor(
                self.problem.id, entry, aux_sources=aux_sources, defines=['-DSIGNATURE_GRADER']
            )
        else:
            raise InternalError('no valid runtime for signature grading %s found' % self.language)
