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

LBM_SRC := upstream/lbm/src
.PHONY: lbm-ref lbm-smoke
lbm-ref:
	rm -rf work/lbm/src && mkdir -p work/lbm/src work/lbm/build/smoke
	cp $(LBM_SRC)/lbm.c $(LBM_SRC)/lbm.h $(LBM_SRC)/lbm_1d_array.h $(LBM_SRC)/config.h work/lbm/src/
	cd work/lbm/src && patch -p1 -s -i ../../../benchmarks/lbm/reference/double-precision.patch
	$(CC) -std=c99 -O2 -ffp-contract=off -DSIZE_X=12 -DSIZE_Y=12 -DSIZE_Z=16 -Iwork/lbm/src \
	  work/lbm/src/lbm.c benchmarks/lbm/reference/ref_main.c -lm -o work/lbm/build/smoke/lbm_ref
lbm-smoke: lbm-ref
	cd work/lbm/build/smoke && ./lbm_ref 64 velocity.dat 2 0 - > stdout.txt && cat stdout.txt
