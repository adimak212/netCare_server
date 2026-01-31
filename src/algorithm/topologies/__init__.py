from .fat_tree import FatTree
from .mesh import Mesh
from .fnn import FNN
from .hybrid import Hybrid
from .sdn import SDN

TOPOLOGIES = {
    FatTree.name: FatTree(),
    Mesh.name: Mesh(),
    FNN.name: FNN(),
    Hybrid.name: Hybrid(),
    SDN.name: SDN(),
}
