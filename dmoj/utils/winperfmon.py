from __future__ import print_function

from ctypes import windll, WinError, byref, Union, Structure, c_double, c_int64
from ctypes.wintypes import HANDLE, LONG, DWORD, LPCWSTR, LPCSTR

import six


def pdh_error_check(result, func, arguments):
    if result:
        raise WinError(result)
    return result


PdhOpenQuery = windll.pdh.PdhOpenQueryW
PdhAddCounter = windll.pdh.PdhAddCounterW
PdhCloseQuery = windll.pdh.PdhCloseQuery
PdhCollectQueryData = windll.pdh.PdhCollectQueryData
PdhGetFormattedCounterValue = windll.pdh.PdhGetFormattedCounterValue
PdhOpenQuery.errcheck = PdhAddCounter.errcheck = PdhCollectQueryData.errcheck = pdh_error_check
PdhGetFormattedCounterValue.errcheck = pdh_error_check

PDH_FMT_RAW = 16
PDH_FMT_ANSI = 32
PDH_FMT_UNICODE = 64
PDH_FMT_LONG = 256
PDH_FMT_DOUBLE = 512
PDH_FMT_LARGE = 1024
PDH_FMT_1000 = 8192
PDH_FMT_NODATA = 16384
PDH_FMT_NOSCALE = 4096
PDH_FMT_NOCAP100 = 32768


class _PDH_Counter_Union(Union):
    _fields_ = [('longValue', LONG),
                ('doubleValue', c_double),
                ('largeValue', c_int64),
                ('AnsiStringValue', LPCSTR),
                ('WideStringValue', LPCWSTR)]


class PDH_FMT_COUNTERVALUE(Structure):
    _anonymous_ = ('union',)
    _fields_ = [('CStatus', DWORD),
                ('union', _PDH_Counter_Union)]


class PerformanceCounter(object):
    def __init__(self, *counters):
        self._query = None
        self._counters = []
        handle = HANDLE()
        PdhOpenQuery(None, 0, byref(handle))
        self._query = handle.value

        for counter in counters:
            if len(counter) == 2:
                path, flags = counter
            else:
                path, flags = counter, PDH_FMT_DOUBLE
            if not isinstance(path, six.text_type):
                path = path.decode('mbcs')
            if not flags & (PDH_FMT_LARGE | PDH_FMT_DOUBLE | PDH_FMT_LONG):
                flags |= PDH_FMT_LONG if flags & PDH_FMT_1000 else PDH_FMT_DOUBLE
            PdhAddCounter(self._query, path, 0, byref(handle))
            self._counters.append((handle.value, flags))

    def close(self):
        if self._query:
            PdhCloseQuery(self._query)

    __del__ = close

    def _query_counter(self, counters):
        (counter, flags) = counters
        data = PDH_FMT_COUNTERVALUE()
        try:
            PdhGetFormattedCounterValue(counter, flags, None, byref(data))
        except WindowsError:
            return 0
        else:
            if flags & PDH_FMT_DOUBLE:
                return data.doubleValue
            elif flags & PDH_FMT_LARGE:
                return data.largeValue
            elif flags & PDH_FMT_LONG:
                return data.longValue

    def query(self):
        PdhCollectQueryData(self._query)
        return map(self._query_counter, self._counters)

    def query_single(self):
        return self.query()[0]


def main():
    from collections import deque
    from time import sleep
    pql_samples = deque(maxlen=5)
    pt_samples = deque(maxlen=5)
    counter = PerformanceCounter(r'\System\Processor Queue Length', r'\Processor(_Total)\% Processor Time')
    try:
        while True:
            pql, pt = counter.query()
            pql_samples.append(pql)
            pt_samples.append(pt)
            print('\rCPU load: %5.3f, %6.2f%%' % (sum(pql_samples) / len(pql_samples), pt), end=' ')
            sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
