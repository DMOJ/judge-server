# DMOJ Judge [![Linux Build Status](https://img.shields.io/travis/SchOJ/udge.svg?logo=linux)](https://travis-ci.org/SchOJ/judge)

Python [AGPLv3](https://github.com/DMOJ/judge/blob/master/LICENSE) contest judge backend for the [DMOJ site](http://github.com/DMOJ/site) interface. See it in action at [dmoj.ca](https://dmoj.ca/)!

<table>
<tr>
<td>
<a href="http://dmoj.ca">
<img src="https://avatars2.githubusercontent.com/u/6934864?v=3&s=100" align="left"></img>
</a>
</td>
<td>
A modern online judge and contest platform system, supporting <b>IO-based</b>, <b>interactive</b>, and <b>signature-graded</b> tasks,
            with <b>runtime data generators</b> and <b>custom output validators</b>.
</td>
</tr>
</table>

## Supported Platforms and Runtimes

The judge implements secure grading on Linux, Windows, and FreeBSD machines.

|           | Linux 	| Windows 	| FreeBSD 	|
|------	|-------	|---------	|---------	|
| x64  	| [✔](https://travis-ci.org/DMOJ/judge)     	| [✔](https://ci.appveyor.com/project/quantum5/judge)        | [✔](https://ci.dmoj.ca/job/dmoj-judge-freebsd/)       	|
| x86  	| ✔     	| ✔      |       ¯\\\_(ツ)\_/¯   |
| x32 	| ✔     	|    &mdash;	|      &mdash;   	|
| ARM  	| ✔     	|      &mdash;   	|      ❌   	|

The DMOJ judge does **not** need a root user to run on Linux machines: it will run just fine under a normal user.

Supported languages include:
* C++ 0x/11/14/17 (GCC and Clang)
* C 99/11
* Java 7/8/9/10
* Python 2/3
* PyPy 2/3
* Pascal
* Perl
* Mono C#/F#/VB

The following runtimes are also supported, but only on Windows machines:
* Visual C++
* C#
* F#
* VB.NET

The judge can also grade in the languages listed below. These languages are less tested and more likely to be buggy.
* Ada
* AWK
* Clozure Common Lisp
* COBOL
* D
* Dart
* Fortran
* Forth
* Go
* Groovy
* Haskell
* INTERCAL
* Kotlin
* Lua
* NASM
* Nim
* Objective-C
* Octave
* OCaml
* PHP 5/7
* Pike
* Prolog
* Racket
* Ruby 2.1
* Rust
* Scala
* Chicken Scheme
* sed
* Steel Bank Common Lisp
* Swift
* Tcl
* Turing
* V8 JavaScript
* Brain****

## Installation
Installing the DMOJ judge creates two executables in your Python's script directory: `dmoj` and `dmoj-cli`.
`dmoj` is used to connect a judge to a DMOJ site instance, while `dmoj-cli` provides a command-line interface to a
local judge, useful for testing problems.

For more detailed steps, read the [Linux Installation](https://docs.dmoj.ca/en/latest/judge/linux_installation/) or [Windows Installation](https://docs.dmoj.ca/en/latest/judge/windows_installation/) instructions.

### Stable Build
[![PyPI version](https://badge.fury.io/py/dmoj.svg)](https://pypi.python.org/pypi/dmoj)
[![PyPI](https://img.shields.io/pypi/pyversions/dmoj.svg)](https://pypi.python.org/pypi/dmoj)

We periodically publish builds [on PyPI](https://pypi.python.org/pypi/dmoj). This is the easiest way to get started,
but may not contain all the latest features and improvements.

```
$ pip install dmoj
```

### Bleeding-Edge Build
This is the version of the codebase we run live on [dmoj.ca](https://dmoj.ca).

```
$ git clone https://github.com/DMOJ/judge.git
$ cd judge
$ git submodule update --init --recursive
$ pip install -e .
```

## Usage
### Running a Judge Server
```
$ dmoj --help
usage: dmoj [-h] [-p SERVER_PORT] -c CONFIG [-l LOG_FILE] [--no-watchdog]
            [-a API_PORT] [-A API_HOST] [-s] [-k] [-T TRUSTED_CERTIFICATES]
            [-e ONLY_EXECUTORS | -x EXCLUDE_EXECUTORS] [--no-ansi]
            server_host [judge_name] [judge_key]

Spawns a judge for a submission server.

positional arguments:
  server_host           host to connect for the server
  judge_name            judge name (overrides configuration)
  judge_key             judge key (overrides configuration)

optional arguments:
  -h, --help            show this help message and exit
  -p SERVER_PORT, --server-port SERVER_PORT
                        port to connect for the server
  -c CONFIG, --config CONFIG
                        file to load judge configurations from
  -l LOG_FILE, --log-file LOG_FILE
                        log file to use
  --no-watchdog         disable use of watchdog on problem directories
  -a API_PORT, --api-port API_PORT
                        port to listen for the judge API (do not expose to
                        public, security is left as an exercise for the
                        reverse proxy)
  -A API_HOST, --api-host API_HOST
                        IPv4 address to listen for judge API
  -s, --secure          connect to server via TLS
  -k, --no-certificate-check
                        do not check TLS certificate
  -T TRUSTED_CERTIFICATES, --trusted-certificates TRUSTED_CERTIFICATES
                        use trusted certificate file instead of system
  -e ONLY_EXECUTORS, --only-executors ONLY_EXECUTORS
                        only listed executors will be loaded (comma-separated)
  -x EXCLUDE_EXECUTORS, --exclude-executors EXCLUDE_EXECUTORS
                        prevent listed executors from loading (comma-
                        separated)
  --no-ansi             disable ANSI output
```

### Running a CLI Judge
```
$ dmoj-cli --help
usage: dmoj-cli [-h] -c CONFIG
                [-e ONLY_EXECUTORS | -x EXCLUDE_EXECUTORS]
                [--no-ansi] [--no-ansi-emu]

Spawns a judge for a submission server.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        file to load judge configurations from
  -e ONLY_EXECUTORS, --only-executors ONLY_EXECUTORS
                        only listed executors will be loaded (comma-separated)
  -x EXCLUDE_EXECUTORS, --exclude-executors EXCLUDE_EXECUTORS
                        prevent listed executors from loading (comma-
                        separated)
  --no-ansi             disable ANSI output
```

## Documentation
For info on the problem file format and more, [read the documentation.](https://docs.dmoj.ca)
