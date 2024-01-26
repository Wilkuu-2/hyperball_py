from typing import List, Tuple
from common import FreqDistribution
from dataclasses import dataclass 
import multiprocessing
from hll import HLLCounter
import networkx 

@dataclass(slots=True)
class DiskEntry(): 
    a: HLLCounter
    Ea: float
    changed: bool = True

@dataclass(slots=True)
class NodeProcessParams(): 
    i: int
    c: List[HLLCounter]
    ni: List[int]
    de: DiskEntry

@dataclass(slots=True)
class NodeProcessOutput():
    i: int
    de: DiskEntry
    nnew: float 
    

class HyperBallDistances():
    __slots__= ('b','C','G','n','distr','disk_store','initialized')

    def __init__(self, b: int, G: networkx.Graph):
        self.b = b
        self.G = G 
        self.n = 0 
        self.disk_store: List[DiskEntry] = []
        self.C: List[HLLCounter] = [] 
        self.distr = FreqDistribution(20)
        self.initialized = False 
    
    def init_counters(self): 
        i = 0 
        for v in self.G.nodes():
            # set the index, so we can access it later 
            self.G.nodes[v]['hb_index'] = i 
            self.C.append(HLLCounter(self.b))
            self.disk_store.append(DiskEntry(None, 0)) #type: ignore
            self.C[i].add(v.to_bytes(8))
            i+= 1

        self.initialized = True
    
    def get_counter(self, i) -> HLLCounter: 
        return self.C[i] 

    def get_index(self, v) -> int:
        return self.G.nodes[v]['hb_index'] 

    def ld_c_disk(self): 
        for i in range(0,len(self.C)):
            self.C[i] = self.disk_store[i].a 

    def create_params(self, v):
        index = self.get_index(v)

        ni = [self.get_index(w) for w in self.G[v]]

        de = self.disk_store[index]
        return NodeProcessParams(index, self.C, ni, de)
    
    def c_deep_copy(self) -> List[HLLCounter]: 
        return [c.copy() for c in self.C] 

    def c_subset_copy(self, ni) -> List[HLLCounter]:
        return [self.C[i].copy() for i in ni]

    def run(self): 
        t = 1
        if not self.initialized:
            self.init_counters() 

        counters_changed = True
        while counters_changed:
            print(f"\rIteration #{t}", end='\n')
            counters_changed = False 
            pl = [self.create_params(v) for v in self.G.nodes()] 
            outs = [process_node(params) for params in pl]
            for out in outs: 
                self.disk_store[out.i] = out.de 
                self.distr.add(t, out.nnew) 
                counters_changed |= out.de.changed 

            self.ld_c_disk()
            t+= 1 
        print("\nDone!")

    def run_parallel(self): 
        pool = multiprocessing.Pool()
        t = 1
        if not self.initialized:
            self.init_counters() 
        
        counters_changed = True
        while counters_changed: 
            #print(f"\rIteration #{t}", end='\n')
            counters_changed = False 

            pl = [self.create_params(v) for v in self.G.nodes()] 
            outs = pool.map(process_node, pl)
            
            for out in outs: 
                self.disk_store[out.i] = out.de 
                self.distr.add(t, out.nnew) 
                counters_changed = counters_changed or out.de.changed 

            self.ld_c_disk()
            t+= 1 

        print("\nDone!")


def list_subset_copy(C, ni) -> List[HLLCounter]:
    return [C[i].copy() for i in ni]
        


def process_node(params: NodeProcessParams) -> NodeProcessOutput:
    #print(f"\rnode: #{params.i}", end='')
    if not params.de.changed:
        return NodeProcessOutput(params.i, params.de,0)
    
    # Expand the ball 
    ch = False 
    a = params.c[params.i].copy()
    # nc = list_subset_copy(params.c, params.ni)
    for w in params.ni: 
        ch |= a.union_ip(params.c[w])
         
    # Add the estimated increase in size to the FreqDistribution
    # self.disk_store[index] if t > 1 else None, 0, True
    Ea = a.getE() 

    de2 = DiskEntry(a, Ea, changed=ch)
    return NodeProcessOutput(params.i, de2, Ea - params.de.Ea)
#     return index, a, Ea, ch


            
def test(): 
    from bfs import BFS_DistanceDistr 
    print("GNP graph")
    g = networkx.fast_gnp_random_graph(2000,0.0232, seed=4209)

    print("HyperBall:")
    h = HyperBallDistances(12, g)
    h.run_parallel() 
    #h.run() 
    print(h.distr.arr)
    print(h.distr.avg())
    d = BFS_DistanceDistr(g)
    print("BFS: Should be correct")
    print(d.count())
    print(d.avg())
    exit()

    print("Complete graph: the average should be 1 exactly") 

    print("HyperBall:")
    g = networkx.complete_graph(200) 
    h = HyperBallDistances(12, g)
    h.run_parallel() 

    print(h.distr.avg())
    d = BFS_DistanceDistr(g)
    print(d.count())
    print(d.avg())




if __name__ == "__main__":
    test()
            
            


    

