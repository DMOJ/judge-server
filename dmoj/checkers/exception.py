from re import split as resplit
from typing import Union

from dmoj.result import CheckerResult
from dmoj.utils.unicode import utf8bytes

verdict = '\u2717\u2713'


def check(
    process_output: bytes, judge_output: bytes, point_value: float = 1, exceptionType: str = '', **kwargs
) -> Union[CheckerResult, bool]:      
    found = kwargs['result'].feedback.split('.')[-1]    
    passed = (found == exceptionType or len(found) > 0 and len(exceptionType) == 0)
    
    if  kwargs['result'].output != '':        
        extended_feedback = ('Any type of exception' if exceptionType == '' else 'An exception of type "' + exceptionType) + '" was expected, but none has been raised:\nYour output: ' + kwargs['result'].output
    else:
        extended_feedback = None if passed else 'An exception was raised, but another exception type was expected:\nRaised: ' + found + '\nExpected: ' + exceptionType

    kwargs['result'].proc_output = ''
    kwargs['result'].result_flag = 0 if passed else 1
        
    return CheckerResult(        
        passed=passed,
        points=point_value,        
        extended_feedback=extended_feedback
    )    

check.run_on_error = True  # type: ignore
