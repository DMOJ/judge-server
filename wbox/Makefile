CC=cl /nologo
LD=cl /nologo
CYTHON=cython
LIBS=netapi32.lib advapi32.lib ole32.lib
PYINCLUDE=.

_wbox.pyd: _wbox.obj handles.obj process.obj user.obj helpers.obj
    $(LD) /LD $** /Fe$@ $(LIBS) $(PYLIB)

process.h: helpers.h
user.h: helpers.h
_wbox.cpp: helpers.h user.h process.h
handles.cpp: handles.h helpers.h
process.cpp: handles.h process.h
user.cpp: user.h
helpers.cpp: helpers.h

_wbox.cpp: _wbox.pyx
    $(CYTHON) --cplus -a _wbox.pyx

.cpp.obj::
    $(CC) /c $< /I$(PYINCLUDE) /EHsc /DUNICODE

clean:
    del /q _wbox.pyd _wbox.obj handles.obj process.obj user.obj helpers.obj _wbox.cpp