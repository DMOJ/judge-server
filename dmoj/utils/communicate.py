import os
import select
import errno
import threading

_PIPE_BUF = getattr(select, 'PIPE_BUF', 512)


class OutputLimitExceeded(Exception):
    pass


if os.name == 'nt':
    from dmoj.utils.winutils import get_handle_of_thread, SYNCHRONIZE, wait_for_multiple_objects


    def _readerthread(fh, buffer, limit, ole):
        read = 0
        while True:
            buf = fh.read(65536)
            if not buf:
                break
            read += len(buf)
            if read > limit:
                ole[0] = True
                break
            buffer.append(buf)


    def safe_communicate(proc, input, outlimit=None, errlimit=None):
        if outlimit is None:
            outlimit = 10485760
        if errlimit is None:
            errlimit = outlimit

        stdout = None  # Return
        stderr = None  # Return

        out_ole = [False]
        err_ole = [False]
        waits = []

        if proc.stdout:
            stdout = []
            stdout_thread = threading.Thread(target=_readerthread, args=(proc.stdout, stdout, outlimit, out_ole))
            stdout_thread.daemon = True
            stdout_thread.start()
            handle = get_handle_of_thread(stdout_thread, SYNCHRONIZE)
            if handle is not None:
                waits.append(handle)

        if proc.stderr:
            stderr = []
            stderr_thread = threading.Thread(target=_readerthread, args=(proc.stderr, stderr, errlimit, err_ole))
            stderr_thread.daemon = True
            stderr_thread.start()
            handle = get_handle_of_thread(stderr_thread, SYNCHRONIZE)
            if handle is not None:
                waits.append(handle)

        if proc.stdin:
            if input is not None:
                try:
                    proc.stdin.write(input)
                except IOError:
                    # IOError: [Errno 22] Invalid argument
                    # Happens when the child ignores stdin data and exits.
                    # There is no way to handle it other than ignore.
                    pass
            try:
                proc.stdin.close()
            except IOError:
                # See above.
                pass

        while waits:
            del waits[wait_for_multiple_objects(waits)]
            if out_ole[0] or err_ole[0]:
                break

        # All data exchanged.  Translate lists into strings.
        if stdout is not None:
            stdout = b''.join(stdout)

        if stderr is not None:
            stderr = b''.join(stderr)

        if out_ole[0] or err_ole[0]:
            raise OutputLimitExceeded('stdout' if out_ole[0] else 'stderr', stdout, stderr)

        proc.wait()
        return stdout, stderr
else:
    def safe_communicate(proc, input, outlimit=None, errlimit=None):
        if outlimit is None:
            outlimit = 10485760
        if errlimit is None:
            errlimit = outlimit
        if proc.stdin:
            # Flush stdio buffer.  This might block, if the user has
            # been writing to .stdin in an uncontrolled fashion.
            proc.stdin.flush()
            if not input:
                proc.stdin.close()

        stdout = None  # Return
        stderr = None  # Return
        fd2file = {}
        fd2output = {}
        fd2length = {}
        fd2limit = {}

        poller = select.poll()

        def register_and_append(file_obj, eventmask):
            poller.register(file_obj.fileno(), eventmask)
            fd2file[file_obj.fileno()] = file_obj

        def close_unregister_and_remove(fd):
            poller.unregister(fd)
            fd2file[fd].close()
            fd2file.pop(fd)

        if proc.stdin and input:
            register_and_append(proc.stdin, select.POLLOUT)

        select_POLLIN_POLLPRI = select.POLLIN | select.POLLPRI
        if proc.stdout:
            register_and_append(proc.stdout, select_POLLIN_POLLPRI)
            fd2output[proc.stdout.fileno()] = stdout = []
            fd2length[proc.stdout.fileno()] = 0
            fd2limit[proc.stdout.fileno()] = outlimit
        if proc.stderr:
            register_and_append(proc.stderr, select_POLLIN_POLLPRI)
            fd2output[proc.stderr.fileno()] = stderr = []
            fd2length[proc.stderr.fileno()] = 0
            fd2limit[proc.stderr.fileno()] = errlimit

        input_offset = 0
        while fd2file:
            try:
                ready = poller.poll()
            except select.error as e:
                if e.args[0] == errno.EINTR:
                    continue
                raise

            for fd, mode in ready:
                if mode & select.POLLOUT:
                    chunk = input[input_offset:input_offset + _PIPE_BUF]
                    try:
                        input_offset += os.write(fd, chunk)
                    except OSError as e:
                        if e.errno == errno.EPIPE:
                            close_unregister_and_remove(fd)
                        else:
                            raise
                    else:
                        if input_offset >= len(input):
                            close_unregister_and_remove(fd)
                elif mode & select_POLLIN_POLLPRI:
                    data = os.read(fd, 4096)
                    if not data:
                        close_unregister_and_remove(fd)
                    fd2output[fd].append(data)
                    fd2length[fd] += len(data)
                    if fd2length[fd] > fd2limit[fd]:
                        if stdout is not None:
                            stdout = b''.join(stdout)
                        if stderr is not None:
                            stderr = b''.join(stderr)

                        raise OutputLimitExceeded(['stderr', 'stdout'][proc.stdout is not None and proc.stdout.fileno() == fd],
                                                  stdout, stderr)
                else:
                    # Ignore hang up or errors.
                    close_unregister_and_remove(fd)

        # All data exchanged.  Translate lists into strings.
        if stdout is not None:
            stdout = b''.join(stdout)
        if stderr is not None:
            stderr = b''.join(stderr)

        proc.wait()
        return stdout, stderr
