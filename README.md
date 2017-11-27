DMOJ Judge [![Linux Build Status](https://img.shields.io/travis/DMOJ/judge.svg?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxODguMSAxOTUuNSI%2BPHBhdGggZmlsbD0iI2ZmZiIgZD0iTTM2LjQgOTcuOGMwIDEwLTggMTguMi0xOC4yIDE4LjJDOC4yIDExNiAwIDEwOCAwIDk3LjhjMC0xMCA4LjItMTguMiAxOC4yLTE4LjJzMTguMiA4IDE4LjIgMTguMnpNMTQwIDE4Ni40YzUgOC43IDE2LjMgMTEuNyAyNSA2LjcgOC43LTUgMTEuNy0xNi4yIDYuNy0yNS01LTguNi0xNi4yLTExLjYtMjUtNi42LTguNiA1LTExLjYgMTYuMi02LjYgMjV6bTMxLjctMTU5YzUtOC43IDItMTkuOC02LjctMjUtOC43LTUtMjAtMi0yNSA2LjgtNSA4LjctMiAyMCA2LjggMjVzMTkuOCAyIDI1LTYuOHpNMTEwIDQ1LjhjMjcuMiAwIDQ5LjQgMjAuOCA1MS44IDQ3LjRsMjYuMy0uNGMtMS0xOS43LTkuNy0zNy41LTIzLTUwLjYtNyAyLjctMTUgMi40LTIyLTEuNy03LTQtMTEuMy0xMS0xMi40LTE4LjMtNi42LTEuNy0xMy41LTIuNy0yMC42LTIuNy0xMi41IDAtMjQuMyAzLTM0LjcgOEw4OCA1MC43YzYuNy0zIDE0LTUgMjItNXptLTUyIDUyYzAtMTcuNiA4LjgtMzMgMjItNDIuNUw2Ni42IDMyLjdDNTEgNDMuMiAzOS4yIDU5LjIgMzQuNCA3Ny43YzUuNyA0LjggOS41IDEyIDkuNSAyMHMtNCAxNS40LTkuNyAyMGM0LjggMTguOCAxNi41IDM0LjggMzIuMiA0NS4zTDgwIDE0MC4zQzY2LjcgMTMxIDU4IDExNS41IDU4IDk4em01MiA1MmMtNy44IDAtMTUuMi0xLjgtMjItNWwtMTIuNiAyMy40YzEwLjMgNS4yIDIyIDggMzQuNiA4IDcgMCAxNC0xIDIwLjYtMi42IDEtNy41IDUuNS0xNC4zIDEyLjUtMTguMyA3LTQuMiAxNS00LjUgMjItMS44IDEzLjMtMTMgMjItMzEgMjMtNTAuNmwtMjYuMi0uNUMxNTkuNCAxMjkgMTM3LjIgMTUwIDExMCAxNTB6Ii8%2BPC9zdmc%2B)](https://travis-ci.org/DMOJ/judge) [![Windows Build Status](https://ci.appveyor.com/api/projects/status/wv4e1eujb6wtcbps?svg=true)](https://ci.appveyor.com/project/quantum5/judge) [![FreeBSD Build Status](https://img.shields.io/jenkins/s/https/ci.dmoj.ca/job/dmoj-judge-freebsd.svg?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHZpZXdCb3g9IjAgMCAyNTYgMjUyIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHByZXNlcnZlQXNwZWN0UmF0aW89InhNaWRZTWlkIj48ZyBmaWxsPSJ3aGl0ZSI%2BPHBhdGggZD0iTTI1Mi43MjMgNS4xMWMxMy41MDggMTMuNS0yMy45MzkgNzIuODQ4LTMwLjI3IDc5LjE4Mi02LjMzIDYuMzIxLTIyLjQwOS41MDUtMzUuOTEtMTMtMTMuNTA4LTEzLjUtMTkuMzI3LTI5LjU4My0xMi45OTYtMzUuOTE0IDYuMzI3LTYuMzMzIDY1LjY3MS00My43NzcgNzkuMTc2LTMwLjI2OU02My4zMDUgMTkuMzk0Yy0yMC42MjItMTEuNy00OS45NjYtMjQuNzE2LTU5LjMtMTUuMzgtOS40NTggOS40NTQgNC4wMzQgMzkuNDU4IDE1Ljg1OCA2MC4xMTdhMTI2LjgxMiAxMjYuODEyIDAgMCAxIDQzLjQ0Mi00NC43MzciLz48cGF0aCBkPSJNMjMyLjEyMyA3OS42MzZjMS44OTkgNi40NCAxLjU1OCAxMS43Ni0xLjUyMiAxNC44MzQtNy4xOTMgNy4xOTYtMjYuNjI0LS40NjQtNDQuMTQtMTcuMTM0YTg5LjM4MyA4OS4zODMgMCAwIDEtMy42MjctMy40MjhjLTYuMzM0LTYuMzM2LTExLjI2Mi0xMy4wOC0xNC40MTQtMTkuMjkxLTYuMTM1LTExLjAwNi03LjY3LTIwLjcyNi0zLjAzMy0yNS4zNjQgMi41MjctMi41MjQgNi41Ny0zLjIxMiAxMS41MDItMi4zMjUgMy4yMTYtMi4wMzQgNy4wMTMtNC4zIDExLjE3Ni02LjYyMS0xNi45MjktOC44My0zNi4xNzYtMTMuODE3LTU2LjU5My0xMy44MTdDNjMuNzUzIDYuNDkgOC44NTQgNjEuMzggOC44NTQgMTI5LjEwNWMwIDY3LjcxMyA1NC45IDEyMi42MSAxMjIuNjE4IDEyMi42MSA2Ny43MiAwIDEyMi42MTYtNTQuODk3IDEyMi42MTYtMTIyLjYxIDAtMjEuODctNS43NC00Mi4zNzctMTUuNzY3LTYwLjE1Ni0yLjE2NyAzLjk1NS00LjI3NCA3LjU3OC02LjE5OCAxMC42ODciLz48L2c%2BPC9zdmc%2B)](https://ci.dmoj.ca/job/dmoj-judge-freebsd/lastBuild/consoleFull) [![Coverage](https://img.shields.io/codecov/c/github/DMOJ/judge.svg)](https://codecov.io/gh/DMOJ/judge) [![Documentation Status](https://readthedocs.org/projects/dmoj/badge/?version=latest)](http://dmoj.readthedocs.org/en/latest/?badge=latest) [![Slack](https://slack.dmoj.ca/badge.svg)](https://slack.dmoj.ca)
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
A modern online judge and contest platform system, supporting <b>IO-based</b>, <b>interactive</b>, and <b>signature-graded</b> tasks.
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

The DMOJ Judge does **not** need a root user to run on Linux machines: it will run just fine under a normal user.

Supported languages include:
* C++ 0x/11/14/17
* C 99/11
* Java 7/8/9/10
* Python 2/3
* PyPy 2/3
* Pascal
* Perl
* Mono C#
* Mono F#
* Mono VB

The following languages are also supported, but only on Windows machines:
* VC 
* C#
* F#
* VB.NET

The Judge can also grade in the languages listed below. These languages are less tested and more likely to be buggy.
* Ada
* AWK
* Clang
* Clang++
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
* Scheme
* sed
* Steel Bank Common Lisp
* Swift
* Tcl
* Turing
* V8 JavaScript
* Brain****

## Installation

On a typical Linux install,

```
$ git clone https://github.com/DMOJ/judge.git
$ cd judge
$ git submodule update --init --recursive
$ python setup.py develop
```

This will create two executables in your Python's script directory: `dmoj` and `dmoj-cli`. `dmoj` is used to connect a judge to a DMOJ site instance, while `dmoj-cli` provides a command-line interface to a local judge, useful for testing problems.

For more detailed steps, read the [Linux Installation](https://docs.dmoj.ca/en/latest/judge/linux_installation/) or [Windows Installation](https://docs.dmoj.ca/en/latest/judge/windows_installation/) instructions.

## Usage
### Running a Judge Server
```
$ dmoj --help
usage: dmoj [-h] [-p SERVER_PORT] -c CONFIG [-l LOG_FILE]
            [-e ONLY_EXECUTORS | -x EXCLUDE_EXECUTORS] [--no-ansi]
            server_host [judge_name] [judge_key]

Spawns a judge for a submission server.

positional arguments:
  server_host           host to listen for the server
  judge_name            judge name (overrides configuration)
  judge_key             judge key (overrides configuration)

optional arguments:
  -h, --help            show this help message and exit
  -p SERVER_PORT, --server-port SERVER_PORT
                        port to listen for the server
  -c CONFIG, --config CONFIG
                        file to load judge configurations from
  -l LOG_FILE, --log-file LOG_FILE
                        log file to use
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
  --no-ansi-emu         disable ANSI emulation on Windows
```

## Documentation
For info on the problem file format and more, 
[read the documentation.](https://docs.dmoj.ca)
