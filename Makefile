CXX ?= c++
SPH_SRC := upstream/sph-exa/src
.PHONY: sph-exa-build sph-exa-smoke
sph-exa-build:
	mkdir -p work/build
	$(CXX) -std=c++14 -O2 -DNDEBUG -Wno-unknown-pragmas -I$(SPH_SRC) -I$(SPH_SRC)/include $(SPH_SRC)/sqpatch.cpp -o work/build/sph-exa
sph-exa-smoke: sph-exa-build
	mkdir -p work/smoke
	cd work/smoke && ../build/sph-exa -n 12 -s 1 -w 1 > stdout.txt

PYTHON ?= python3
.PHONY: start run status watch stop test
start:
	$(PYTHON) tools/runner.py start
run:
	$(PYTHON) tools/runner.py run
status:
	$(PYTHON) tools/runner.py status
watch:
	$(PYTHON) tools/runner.py watch
stop:
	$(PYTHON) tools/runner.py stop
test:
	$(PYTHON) -m unittest discover -s tests -v
