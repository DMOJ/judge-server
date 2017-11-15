DMOJ Judge [![Linux Build Status](https://img.shields.io/travis/DMOJ/judge.svg?maxAge=2592000)](https://travis-ci.org/DMOJ/judge) [![Windows Build Status](https://ci.appveyor.com/api/projects/status/wv4e1eujb6wtcbps?svg=true)](https://ci.appveyor.com/project/quantum5/judge) [![FreeBSD Build Status](https://ci.dmoj.ca/buildStatus/icon?job=dmoj-judge-freebsd)](https://ci.dmoj.ca/job/dmoj-judge-freebsd/) [![Coverage](https://img.shields.io/codecov/c/github/DMOJ/judge.svg)](https://codecov.io/gh/DMOJ/judge) [![Slack](https://slack.dmoj.ca/badge.svg)](https://slack.dmoj.ca)
=====

Python [AGPLv3](https://github.com/DMOJ/judge/blob/master/LICENSE) contest judge backend for the [DMOJ site](http://github.com/DMOJ/site) interface. The judge implements secure grading on Linux, Windows, and FreeBSD machines.

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

The DMOJ Judge does **not** need a root user to run on Linux machines: it will run just fine under a normal user.

Supported languages include:
* C/++/0x/11/14/
* Java 7/8
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
* R
* Racket
* Ruby 2.1
* Rust
* Scala
* Scheme
* sed
* Swift
* Tcl
* Turing
* V8 JavaScript
* Brain****

## Installation
```
$ git clone https://github.com/DMOJ/judge.git
$ cd judge
$ python setup.py develop
```

This will create two executables in your Python's script directory: `dmoj` and `dmoj-cli`. `dmoj` is used to connect a judge to a DMOJ site instance, while `dmoj-cli` provides a command-line interface to a local judge, useful for testing problems.

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

## More Help
For info on the problem file format and more, 
[read the documentation.](https://docs.dmoj.ca)
