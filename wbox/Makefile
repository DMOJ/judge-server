CC=cl /nologo
LD=cl /nologo
CFLAGS=/Ox /EHsc /DUNICODE /W4 /GL
LDFLAGS=/OPT:REF,ICF /LTCG
CYTHON=cython
LIBS=netapi32.lib advapi32.lib ole32.lib

!IFDEF PYINCLUDE
CFLAGS=$(CFLAGS) /I$(PYINCLUDE)
!ENDIF

_wbox.pyd: _wbox.obj handles.obj process.obj user.obj helpers.obj firewall.obj
    $(LD) /LD $** /Fe$@ $(LIBS) $(PYLIB) /link $(LDFLAGS)

process.h: helpers.h
user.h: helpers.h
_wbox.cpp: helpers.h user.h process.h firewall.h
firewall.cpp: firewall.h helpers.h
handles.cpp: handles.h helpers.h
process.cpp: handles.h process.h
user.cpp: user.h
helpers.cpp: helpers.h

_wbox.cpp: _wbox.pyx
    $(CYTHON) --cplus -a _wbox.pyx

.cpp.obj::
    $(CC) $(CFLAGS) /c $<

clean:
    del /q _wbox.pyd _wbox.obj handles.obj process.obj user.obj helpers.obj _wbox.cpp