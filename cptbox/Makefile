CXX=g++
CXXFLAGS=-g -fPIC -Wall
LIBS=-lrt
SOURCES=ptbox.cpp ptdebug.cpp ptdebug32.cpp ptdebug64.cpp ptproc.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=ptbox

all: $(SOURCES) $(EXECUTABLE) cptbox.so

$(EXECUTABLE): $(OBJECTS)
	$(CXX) $(CXXFLAGS) -o $@ $(OBJECTS) $(LIBS)

ptbox.cpp: ptbox.h
ptdebug.cpp: ptbox.h
ptdebug32.cpp: ptbox.h
ptdebug64.cpp: ptbox.h
ptproc.cpp: ptbox.h

.cpp.o:
	$(CXX) $(CXXFLAGS) -c -o $@ $<

cptbox.so: cptbox.o $(OBJECTS)
	$(CXX) -shared $(CXXFLAGS) -o $@ $(OBJECTS) cptbox.o $(LIBS) -lpython$(PYVER)

cptbox.cpp: cptbox.pyx
	cython --cplus cptbox.pyx
