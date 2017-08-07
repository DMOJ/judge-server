import os

import yaml

config = yaml.safe_load(r'''tempdir: C:\judgetemp
runtime:
  awk: C:\Program Files\Git\usr\bin\awk.exe
  csc: C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe
  cl.exe: C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\cl.exe
  go: C:\go\bin\go.exe
  java: C:\Program Files (x86)\Java\jre7\bin\java.exe
  javac: C:\Program Files (x86)\Java\jdk1.7.0\bin\javac.exe
  java8: C:\Program Files (x86)\Java\jre8\bin\java.exe
  javac8: C:\Program Files (x86)\Java\jdk1.8.0\bin\javac.exe
  perl: C:\Perl\bin\perl.exe
  python: C:\Python27\Python.exe
  python3: C:\Python35\Python.exe
  ruby19: C:\Ruby193\bin\ruby.exe
  ruby2: C:\Ruby21\bin\ruby.exe
  sed: C:\Program Files\Git\usr\bin\sed.exe
  vbc: C:\Windows\Microsoft.NET\Framework\v4.0.30319\vbc.exe

  go_env:
    PATH: C:\go\bin
''')

runtime = config['runtime']

try:
    gcc_bin = next(dir for dir, dirs, files in os.walk(r'C:\mingw-w64') if 'gcc.exe' in files)
except StopIteration:
    pass
else:
    runtime['gcc_env'] = {'PATH': gcc_bin}
    runtime['gcc'] = os.path.join(gcc_bin, 'gcc.exe')
    runtime['g++'] = runtime['g++11'] = os.path.join(gcc_bin, 'g++.exe')
    runtime['gfortran'] = os.path.join(gcc_bin, 'gfortran.exe')

print yaml.safe_dump(config)
