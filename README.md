DMOJ Judge [![Linux Build Status](https://img.shields.io/travis/DMOJ/judge.svg?logo=linux)](https://travis-ci.org/DMOJ/judge) [![FreeBSD Build Status](https://img.shields.io/jenkins/s/https/ci.dmoj.ca/job/dmoj-judge-freebsd.svg?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHZpZXdCb3g9IjAgMCAyNTYgMjUyIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHByZXNlcnZlQXNwZWN0UmF0aW89InhNaWRZTWlkIj48ZyBmaWxsPSJ3aGl0ZSI%2BPHBhdGggZD0iTTI1Mi43MjMgNS4xMWMxMy41MDggMTMuNS0yMy45MzkgNzIuODQ4LTMwLjI3IDc5LjE4Mi02LjMzIDYuMzIxLTIyLjQwOS41MDUtMzUuOTEtMTMtMTMuNTA4LTEzLjUtMTkuMzI3LTI5LjU4My0xMi45OTYtMzUuOTE0IDYuMzI3LTYuMzMzIDY1LjY3MS00My43NzcgNzkuMTc2LTMwLjI2OU02My4zMDUgMTkuMzk0Yy0yMC42MjItMTEuNy00OS45NjYtMjQuNzE2LTU5LjMtMTUuMzgtOS40NTggOS40NTQgNC4wMzQgMzkuNDU4IDE1Ljg1OCA2MC4xMTdhMTI2LjgxMiAxMjYuODEyIDAgMCAxIDQzLjQ0Mi00NC43MzciLz48cGF0aCBkPSJNMjMyLjEyMyA3OS42MzZjMS44OTkgNi40NCAxLjU1OCAxMS43Ni0xLjUyMiAxNC44MzQtNy4xOTMgNy4xOTYtMjYuNjI0LS40NjQtNDQuMTQtMTcuMTM0YTg5LjM4MyA4OS4zODMgMCAwIDEtMy42MjctMy40MjhjLTYuMzM0LTYuMzM2LTExLjI2Mi0xMy4wOC0xNC40MTQtMTkuMjkxLTYuMTM1LTExLjAwNi03LjY3LTIwLjcyNi0zLjAzMy0yNS4zNjQgMi41MjctMi41MjQgNi41Ny0zLjIxMiAxMS41MDItMi4zMjUgMy4yMTYtMi4wMzQgNy4wMTMtNC4zIDExLjE3Ni02LjYyMS0xNi45MjktOC44My0zNi4xNzYtMTMuODE3LTU2LjU5My0xMy44MTdDNjMuNzUzIDYuNDkgOC44NTQgNjEuMzggOC44NTQgMTI5LjEwNWMwIDY3LjcxMyA1NC45IDEyMi42MSAxMjIuNjE4IDEyMi42MSA2Ny43MiAwIDEyMi42MTYtNTQuODk3IDEyMi42MTYtMTIyLjYxIDAtMjEuODctNS43NC00Mi4zNzctMTUuNzY3LTYwLjE1Ni0yLjE2NyAzLjk1NS00LjI3NCA3LjU3OC02LjE5OCAxMC42ODciLz48L2c%2BPC9zdmc%2B)](https://ci.dmoj.ca/job/dmoj-judge-freebsd/lastBuild/consoleFull) [![Coverage](https://img.shields.io/codecov/c/github/DMOJ/judge.svg)](https://codecov.io/gh/DMOJ/judge) [![Documentation Status](https://readthedocs.org/projects/dmoj/badge/?version=latest)](https://docs.dmoj.ca) [![Slack](https://slack.dmoj.ca/badge.svg)](https://slack.dmoj.ca)
=====

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

The judge implements secure grading on Linux and FreeBSD machines.

|           | Linux 	| FreeBSD 	|
|------	|-------	|---------	|
| x64  	| [✔](https://travis-ci.org/DMOJ/judge)     	| [✔](https://ci.dmoj.ca/job/dmoj-judge-freebsd/)       	|
| x86  	| ✔     	|       ¯\\\_(ツ)\_/¯   |
| x32 	| ✔     	|      &mdash;   	|
| ARM  	| ✔     	|      ❌   	|

Versions up to and including [v1.4.0](https://github.com/DMOJ/judge/releases/tag/v1.4.0) also supported grading on Windows machines.

The DMOJ judge does **not** need a root user to run on Linux machines: it will run just fine under a normal user.

Supported languages include:
* C++ 11/14/17 (GCC and Clang)
* C 99/11
* Java 8/9/10/11
* Python 2/3
* PyPy 2/3
* Pascal
* Perl
* Mono C#/F#/VB

The judge can also grade in the languages listed below. These languages are less tested and more likely to be buggy.
* Ada
* AWK
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
* Objective-C
* OCaml
* PHP
* Pike
* Prolog
* Racket
* Ruby
* Rust
* Scala
* Chicken Scheme
* sed
* Steel Bank Common Lisp
* Swift
* Tcl
* Turing
* V8 JavaScript
* Brain\*\*\*\*

## Installation
Installing the DMOJ judge creates two executables in your Python's script directory: `dmoj` and `dmoj-cli`.
`dmoj` is used to connect a judge to a DMOJ site instance, while `dmoj-cli` provides a command-line interface to a
local judge, useful for testing problems.

For more detailed steps, read the [installation instructions](https://docs.dmoj.ca/#/judge/linux_installation).

Note that **the only officially-supported Linux distribution is the latest Debian**, with the default `apt` versions of all runtimes. This is [what we run on dmoj.ca](https://dmoj.ca/runtimes/matrix/), and it should "just work". While the judge will likely still work with other distributions and runtime versions, some runtimes might fail to initialize. In these cases, please [file an issue](https://github.com/DMOJ/judge/issues).

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

Several environment variables can be specified to control the compilation of the sandbox:

* `DMOJ_USE_SECCOMP`; set it to `no` if you're building on a pre-Linux 3.5 kernel to disable `seccomp` filtering in favour of pure `ptrace` (slower).
   This flag has no effect when building outside of Linux.
* `DMOJ_TARGET_ARCH`; use it to override the default architecture specified for compiling the sandbox (via `-march`).
   Usually this is `native`, but will not be specified on ARM unless `DMOJ_TARGET_ARCH` is set (a generic, slow build will be compiled instead).

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
                [--no-ansi]

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
