// Separate instrumentation: physics, constants and update order are upstream's.
#include <fstream>
#include <iomanip>
#include <numeric>
#include <stdexcept>
#include <string>
#include "sphexa.hpp"
#include "SqPatch.hpp"
using namespace sphexa;

static void snapshot(const std::string& prefix, const SqPatch<double>& d) {
    std::ofstream fields(prefix + ".tsv"), meta(prefix + ".meta");
    if (!fields || !meta) throw std::runtime_error("Cannot create snapshot");
    fields << std::setprecision(17);
    for (int i = 0; i < d.count; ++i) {
        fields << i;
        for (auto field : d.data) fields << ' ' << (*field)[i];
        fields << '\n';
    }
    meta << std::setprecision(17)
         << d.ttot << ' ' << d.etot << ' ' << d.ecin << ' ' << d.eint << ' '
         << d.bbox.xmin << ' ' << d.bbox.xmax << ' '
         << d.bbox.ymin << ' ' << d.bbox.ymax << ' '
         << d.bbox.zmin << ' ' << d.bbox.zmax << '\n';
}

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    const int side = std::stoi(argv[1]), updates = std::stoi(argv[2]);
    const std::string out = argv[3]; // Existing directory; updates is a count, not maxStep.
    if (side < 12 || updates < 1) return 2;
    SqPatch<double> d(side);
    DistributedDomain<double> distributedDomain;
    Domain<double, Octree<double>> domain(d.ngmin, d.ng0, d.ngmax);
    std::vector<int> clist(d.count);
    std::iota(clist.begin(), clist.end(), 0);
    std::ofstream constants(out + "/constants.txt");
    snapshot(out + "/init", d);
    for (d.iteration = 0; d.iteration < updates; ++d.iteration) {
        const auto prefix = out + "/i" + std::to_string(d.iteration) + "-";
        d.resize(d.count);
        distributedDomain.distribute(clist, d);
        distributedDomain.synchronizeHalos(&d.x, &d.y, &d.z, &d.h, &d.m);
        domain.buildTree(d);
        domain.findNeighbors(clist, d);
        snapshot(prefix + "geometry", d);
        {
            std::ofstream neighbors(prefix + "neighbors.tsv");
            for (int i = 0; i < d.count; ++i) {
                neighbors << i;
                for (int j = 0; j < d.neighborsCount[i]; ++j)
                    neighbors << ' ' << d.neighbors[i*d.ngmax+j];
                neighbors << '\n';
            }
        }
        sph::computeDensity<double>(clist, d);
        snapshot(prefix + "density", d);
        if (d.iteration == 0) sph::initFluidDensityAtRest<double>(clist, d);
        snapshot(prefix + "rest", d);
        sph::computeEquationOfState<double>(clist, d);
        snapshot(prefix + "eos", d);
        distributedDomain.resizeArrays(d.count, &d.vx, &d.vy, &d.vz, &d.ro, &d.p, &d.c);
        distributedDomain.synchronizeHalos(&d.vx, &d.vy, &d.vz, &d.ro, &d.p, &d.c);
        sph::computeIAD<double>(clist, d);
        snapshot(prefix + "iad", d);
        distributedDomain.resizeArrays(d.count, &d.c11, &d.c12, &d.c13, &d.c22, &d.c23, &d.c33);
        distributedDomain.synchronizeHalos(&d.c11, &d.c12, &d.c13, &d.c22, &d.c23, &d.c33);
        sph::computeMomentumAndEnergyIAD<double>(clist, d);
        snapshot(prefix + "momentum", d);
        sph::computeTimestep<double>(clist, d);
        snapshot(prefix + "timestep", d);
        sph::computePositions<double>(clist, d);
        snapshot(prefix + "positions", d);
        sph::computeTotalEnergy<double>(clist, d);
        snapshot(prefix + "energy", d);
        const auto totalNeighbors = domain.neighborsSum(clist, d);
        std::ofstream dump(out + "/dump" + std::to_string(d.iteration) + ".txt");
        d.writeData(clist, dump);
        d.writeConstants(d.iteration, totalNeighbors, constants);
    }
}
