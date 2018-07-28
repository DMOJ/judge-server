import uuid

from dmoj.error import CompileError
from dmoj.executors import executors
from dmoj.graders import StandardGrader
from dmoj.utils import ansi
from dmoj.utils.unicode import utf8bytes


class SignatureGrader(StandardGrader):
    def _generate_binary(self):
        siggraders = ('C', 'CPP03', 'CPP0X', 'CPP11', 'CPP14', 'CPP17')

        for i in reversed(siggraders):
            if i in executors:
                siggrader = i
                break
        else:
            raise CompileError(b"can't signature grade, why did I get this submission?")
        if self.language in siggraders:
            aux_sources = {}
            handler_data = self.problem.config['signature_grader']

            entry_point = self.problem.problem_data[handler_data['entry']]
            header = self.problem.problem_data[handler_data['header']]

            submission_prefix = (
                '#include "%s"\n'
                '#define main main_%s\n'
            ) % (handler_data['header'], str(uuid.uuid4()).replace('-', ''))

            aux_sources[self.problem.id + '_submission'] = utf8bytes(submission_prefix) + self.source

            aux_sources[handler_data['header']] = header
            entry = entry_point
            # Compile as CPP regardless of what the submission language is
            try:
                return executors[siggrader].Executor(self.problem.id, entry, aux_sources=aux_sources,
                                                     writable=handler_data['writable'] or (1, 2),
                                                     fds=handler_data['fds'], defines=['-DSIGNATURE_GRADER'])
            except CompileError as compilation_error:
                self.judge.packet_manager.compile_error_packet(ansi.format_ansi(
                    compilation_error.args[0] or 'compiler exited abnormally'
                ))

                # Compile error is fatal
                raise

        self.judge.packet_manager.compile_error_packet('no valid handler compiler exists')
