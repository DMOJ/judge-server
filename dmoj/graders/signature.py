import uuid

from dmoj.error import CompileError
from dmoj.executors import executors
from dmoj.graders import StandardGrader


class SignatureGrader(StandardGrader):
    def _generate_binary(self):
        siggraders = ('C', 'CPP', 'CPP0X', 'CPP11', 'CPP14')

        for i in reversed(siggraders):
            if i in executors:
                siggrader = i
                break
        else:
            raise CompileError("can't signature grade, why did I get this submission?")
        if self.language in siggraders:
            aux_sources = {}
            handler_data = self.problem.config['handler']

            entry_point = self.problem.problem_data[handler_data['entry']]
            header = self.problem.problem_data[handler_data['header']]

            aux_sources[self.problem.id + '_submission'] = (
                                                               '#include "%s"\n#define main main_%s\n' %
                                                               (handler_data['header'],
                                                                str(uuid.uuid4()).replace('-',
                                                                                          ''))) + self.source
            aux_sources[handler_data['header']] = header
            entry = entry_point
            # Compile as CPP11 regardless of what the submission language is
            try:
                return executors[siggrader].Executor(self.problem.id, entry, aux_sources=aux_sources,
                                                     writable=handler_data['writable'] or (1, 2),
                                                     fds=handler_data['fds'])
            except CompileError as compilation_error:
                self.judge.packet_manager.compile_error_packet(compilation_error.message)

                # Compile error is fatal
                return None

        self.judge.packet_manager.compile_error_packet('no valid handler compiler exists')