CXX=g++
CXXFLAGS=-g -fPIC -Wall -O3 -march=native
LIBS=-lrt
SOURCES=ptbox.cpp ptdebug.cpp ptdebug32.cpp ptdebug64.cpp ptproc.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=ptbox

all: $(SOURCES) $(EXECUTABLE) _cptbox.so

$(EXECUTABLE): $(OBJECTS)
	$(CXX) $(CXXFLAGS) -o $@ $(OBJECTS) $(LIBS)

strip: $(EXECUTABLE) _cptbox.so
	strip -s $(EXECUTABLE) _cptbox.so

ptbox.cpp: ptbox.h
ptdebug.cpp: ptbox.h
ptdebug32.cpp: ptbox.h
ptdebug64.cpp: ptbox.h
ptproc.cpp: ptbox.h

.cpp.o:
	$(CXX) $(CXXFLAGS) -c -o $@ $<

_cptbox.so: _cptbox.o $(OBJECTS)
	$(CXX) -shared $(CXXFLAGS) -o $@ $(OBJECTS) _cptbox.o $(LIBS) -lpython$(PYVER)

_cptbox.cpp: _cptbox.pyx
	cython --cplus _cptbox.pyx

clean:
	-rm -f $(OBJECTS) _cptbox.so $(EXECUTABLE) _cptbox.cpp _cptbox.o