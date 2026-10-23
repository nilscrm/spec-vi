// Diagnostic only: replay unchanged upstream density with saved geometry/neighbor order.
#include <fstream>
#include <iomanip>
#include <numeric>
#include <string>
#include "sphexa.hpp"
#include "SqPatch.hpp"
using namespace sphexa;
int main(int argc,char**argv){
 if(argc!=6)return 2;
 int side=std::stoi(argv[1]);SqPatch<double>d(side);std::ifstream state(argv[2]),meta(argv[3]),neighbors(argv[4]);
 for(int i=0;i<d.count;++i){int id;state>>id;if(id!=i)return 3;for(auto f:d.data)state>>(*f)[i];}
 meta>>d.ttot>>d.etot>>d.ecin>>d.eint>>d.bbox.xmin>>d.bbox.xmax>>d.bbox.ymin>>d.bbox.ymax>>d.bbox.zmin>>d.bbox.zmax;
 d.neighbors.resize(d.count*d.ngmax);d.neighborsCount.resize(d.count);
 std::string line;for(int i=0;i<d.count;++i){std::getline(neighbors,line);std::istringstream in(line);int id,j;in>>id;if(id!=i)return 4;int k=0;while(in>>j)d.neighbors[i*d.ngmax+k++]=j;d.neighborsCount[i]=k;}
 std::vector<int>clist(d.count);std::iota(clist.begin(),clist.end(),0);sph::computeDensity<double>(clist,d);
 std::ofstream out(argv[5]);out<<std::setprecision(17);for(int i=0;i<d.count;++i)out<<i<<' '<<d.ro[i]<<'\n';
 return state&&meta?0:5;
}
