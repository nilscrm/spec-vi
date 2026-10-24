/* Reference driver for the pinned LBM kernel (spec-vi adaptation, not upstream).
 *
 * Replaces the Parboil harness (main.c, parboil.h timers and argument parser) with the
 * SPEC CPU 470.lbm-style command line, and adds full-state dumps for validation:
 *
 *   lbm_ref <time steps> <result file> <0: nil, 2: store> <0: ldc, 1: channel>
 *           [<obstacle file> | -] [--dump <state file>]
 *
 * The time-step loop, initialization order and final statistics follow upstream main.c.
 * The grid size is fixed at compile time with -DSIZE_X/-DSIZE_Y/-DSIZE_Z, as upstream.
 *
 * --dump writes the initial state and the state after every time step, for the swept
 * region z in [0, SIZE_Z), cells in x-fastest order. Each record is the 19 distribution
 * values (binary64, little-endian) of one cell. The flag word of every cell is written
 * once, before the first state, as one little-endian uint32 per cell.
 */
#include "lbm.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static LBM_GridPtr srcGrid, dstGrid;

static void dump_flags(FILE* f, LBM_Grid grid) {
	int x, y, z;
	for (z = 0; z < SIZE_Z; z++)
		for (y = 0; y < SIZE_Y; y++)
			for (x = 0; x < SIZE_X; x++) {
				unsigned int flags = *MAGIC_CAST(GRID_ENTRY(grid, x, y, z, FLAGS));
				fwrite(&flags, sizeof flags, 1, f);
			}
}

static void dump_state(FILE* f, LBM_Grid grid) {
	int x, y, z;
	for (z = 0; z < SIZE_Z; z++)
		for (y = 0; y < SIZE_Y; y++)
			for (x = 0; x < SIZE_X; x++)
				fwrite(&GRID_ENTRY(grid, x, y, z, C), sizeof(double), N_DISTR_FUNCS, f);
}

int main(int nArgs, char* arg[]) {
	int t, nTimeSteps, action, simType;
	const char *resultFilename, *obstacleFilename = NULL, *dumpFilename = NULL;
	FILE* dump = NULL;
	int i;

	if (nArgs < 5) {
		printf("syntax: lbm_ref <time steps> <result file> <0: nil, 2: store> "
		       "<0: ldc, 1: channel flow> [<obstacle file> | -] [--dump <file>]\n");
		return 1;
	}
	nTimeSteps = atoi(arg[1]);
	resultFilename = arg[2];
	action = atoi(arg[3]);
	simType = atoi(arg[4]);
	for (i = 5; i < nArgs; i++) {
		if (strcmp(arg[i], "--dump") == 0 && i + 1 < nArgs) dumpFilename = arg[++i];
		else if (strcmp(arg[i], "-") != 0) obstacleFilename = arg[i];
	}
	if ((action != 0 && action != 2) || (simType != 0 && simType != 1)) {
		printf("unsupported action/simType\n");
		return 1;
	}

	printf("grid size: %i x %i x %i, nTimeSteps: %i, simType: %s, obstacle file: %s\n",
	       SIZE_X, SIZE_Y, SIZE_Z, nTimeSteps, simType ? "channel flow" : "lid-driven cavity",
	       obstacleFilename ? obstacleFilename : "<none>");

	LBM_allocateGrid((double**)&srcGrid);
	LBM_allocateGrid((double**)&dstGrid);
	LBM_initializeGrid(*srcGrid);
	LBM_initializeGrid(*dstGrid);
	if (obstacleFilename != NULL) {
		LBM_loadObstacleFile(*srcGrid, obstacleFilename);
		LBM_loadObstacleFile(*dstGrid, obstacleFilename);
	}
	if (simType == 1) {
		LBM_initializeSpecialCellsForChannel(*srcGrid);
		LBM_initializeSpecialCellsForChannel(*dstGrid);
	} else {
		LBM_initializeSpecialCellsForLDC(*srcGrid);
		LBM_initializeSpecialCellsForLDC(*dstGrid);
	}
	LBM_showGridStatistics(*srcGrid);

	if (dumpFilename) {
		dump = fopen(dumpFilename, "wb");
		if (!dump) { printf("cannot open dump file\n"); return 1; }
		dump_flags(dump, *srcGrid);
		dump_state(dump, *srcGrid);
	}

	for (t = 1; t <= nTimeSteps; t++) {
		if (simType == 1) LBM_handleInOutFlow(*srcGrid);
		LBM_performStreamCollide(*srcGrid, *dstGrid);
		LBM_swapGrids(&srcGrid, &dstGrid);
		if (dump) dump_state(dump, *srcGrid);
		if ((t & 63) == 0) printf("timestep: %i\n", t);
	}

	LBM_showGridStatistics(*srcGrid);
	if (action == 2) LBM_storeVelocityField(*srcGrid, resultFilename, TRUE);
	if (dump) fclose(dump);
	LBM_freeGrid((double**)&srcGrid);
	LBM_freeGrid((double**)&dstGrid);
	return 0;
}
