import Queue
import cStringIO
import threading
import traceback

from dmoj.graders import StandardGrader
from dmoj.result import Result
from dmoj.utils.module import load_module


class InteractiveGrader(StandardGrader):
    def _interact_with_process(self, case, result):
        process = self._current_proc

        try:
            grader_filename = self.problem.config.grader
            interactive_grader = load_module('<interactive grader>', self.problem.problem_data[grader_filename],
                                             filename=grader_filename)
        except:
            traceback.print_exc()
            raise IOError('could not load grader module')

        try:
            return_queue = Queue.Queue()

            def interactive_thread(interactor, Q, case_number, process, case_input, case_output, point_value,
                                   source_code):
                Q.put_nowait(interactor(case_number, process, case_input=case_input, case_output=case_output,
                                        point_value=point_value, source_code=source_code))

            input_data = case.input_data()
            output_data = case.output_data()
            ithread = threading.Thread(target=interactive_thread, args=(
                interactive_grader.grade, return_queue, case.position, process,
                input_data and cStringIO.StringIO(input_data),
                output_data and cStringIO.StringIO(output_data), case.points, self.source))
            ithread.start()
            ithread.join(self.problem.time_limit + 1.0)
            if ithread.is_alive():
                result.result_flag = Result.TLE
                error = ''
            else:
                result = return_queue.get_nowait()
                if isinstance(result, tuple) or isinstance(result, list):
                    result, error = result
                else:
                    error = ''
        except:
            traceback.print_exc()
            try:
                process.kill()
            except:  # The process might've already exited
                pass
            self.judge.packet_manager.internal_error_packet(self.problem.id + '\n\n' + traceback.format_exc())
            return
        else:
            process.wait()
        return error