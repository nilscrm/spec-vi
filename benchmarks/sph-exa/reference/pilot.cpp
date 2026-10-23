// Instrumentation only: all reference physics and initialization come from upstream.
#include <iomanip>
#include <iostream>
#include <numeric>
#include "sphexa.hpp"
#include "SqPatch.hpp"
int main(int argc, char** argv) {
    if (argc != 3) return 2;
    int side = std::stoi(argv[1]);
    std::string mode = argv[2];
    if (side < 12 || side > 64) return 2;
    SqPatch<double> d(side);
    std::cout << std::setprecision(17);
    if (mode == "init") {
        for (int i=0; i<d.n; ++i) {
            for (auto field : d.data) std::cout << (*field)[i] << ' ';
            std::cout << '\n';
        }
    } else if (mode == "density") {
        std::vector<int> ids(d.n);
        std::iota(ids.begin(), ids.end(), 0);
        sphexa::Domain<double> domain(d.ngmin, d.ng0, d.ngmax);
        domain.buildTree(d);
        domain.findNeighbors(ids,d);
        sphexa::sph::computeDensity<double>(ids,d);
        // Structured stream: center then all upstream-selected neighbors, plus expected density.
        for (int i=0; i<d.n; ++i) {
            std::cout << i << ' ' << d.x[i] << ' ' << d.y[i] << ' ' << d.z[i] << ' '
                      << d.h[i] << ' ' << d.m[i] << ' ' << d.ro[i] << ' ' << d.neighborsCount[i] << ' ' << (d.bbox.zmax-d.bbox.zmin);
            for (int j=0; j<d.neighborsCount[i]; ++j) {
                int k = d.neighbors[i*d.ngmax+j];
                std::cout << ' ' << k << ' ' << d.x[k] << ' ' << d.y[k] << ' ' << d.z[k] << ' ' << d.m[k];
            }
            std::cout << '\n';
        }
    } else return 2;
}
