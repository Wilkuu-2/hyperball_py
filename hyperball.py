from typing import List
from common import FreqDistribution
from dataclasses import dataclass 
import multiprocessing
from hll import HLLCounter
import networkx 


@dataclass(slots=True)
class DiskEntry(): 
    """ Stuff saved from last iteration """
    a: HLLCounter
    Ea: float
    changed: bool = True

@dataclass(slots=True)
class NodeProcessParams(): 
    """Stuff we pass to the process_node function"""
    i: int
    c: List[HLLCounter]
    ni: List[int]
    de: DiskEntry

@dataclass(slots=True)
class NodeProcessOutput():
    """Stuff we get from the process_node function"""
    i: int
    de: DiskEntry
    nnew: float 
    

class HyperBallDistances():
    """ The class that keeps the state of the HyperBall process"""
        
    # All the variables
    __slots__= ('b','C','G','n','distr','disk_store','initialized')

    def __init__(self, b: int, G: networkx.Graph):
        """Constuctor"""
        self.b = b
        self.G = G 
        self.n = 0 
        self.disk_store: List[DiskEntry] = []
        self.C: List[HLLCounter] = [] 
        self.distr = FreqDistribution(20)
        self.initialized = False 
   
    def init_counters(self): 
        """Initalize the counters along with other things"""
        i = 0 
        for v in self.G.nodes():
            # set the index, so we can access it later 
            self.G.nodes[v]['hb_index'] = i 
            self.C.append(HLLCounter(self.b))
            # It's safe to save None here, since we know that we won't access a before it's changed
            self.disk_store.append(DiskEntry(None, 0)) #type: ignore
            self.C[i].add(v.to_bytes(8))
            i+= 1

        self.initialized = True
    

    def get_index(self, v) -> int:
        """Get the index of the node from it's data"""
        return self.G.nodes[v]['hb_index'] 

    def ld_c_disk(self): 
        """Loads the information from the disk_store to the active counter store C """
        for i in range(0,len(self.C)):
            self.C[i] = self.disk_store[i].a 

    def create_params(self, v):
        """Helper to create parameters for process_node"""
        index = self.get_index(v)

        ni = [self.get_index(w) for w in self.G[v]]

        de = self.disk_store[index]
        return NodeProcessParams(index, self.C, ni, de)
    
        
    def run(self): 
        """Non paralellized version of the algorithm"""
        t = 1
        if not self.initialized:
            self.init_counters() 

        counters_changed = True
        while counters_changed:
            counters_changed = False 

            # Create parameters for each node and pass them to process_node  
            outs = [process_node(self.create_params(v)) for v in self.G.nodes()] 
            
            # Process the output 
            for out in outs: 
                # Store the disk results 
                self.disk_store[out.i] = out.de 
                # Add the difference in ball cardinality to the FreqDistribution
                self.distr.add(t, out.nnew) 
                # See if the counter changed
                counters_changed |= out.de.changed 

            # Load disk_store to C 
            self.ld_c_disk()

            t+= 1 

    def run_parallel(self): 
        """paralellized version of the algorithm"""
        # initialize the threadpool 
        pool = multiprocessing.Pool()
        t = 1

        if not self.initialized:
            self.init_counters() 
        
        counters_changed = True
        while counters_changed: 
            counters_changed = False 
            
            # Create the parameters for each node and process them in the threadpool  
            outs = pool.map(process_node, [self.create_params(v) for v in self.G.nodes()] )
            
            # Process the output 
            for out in outs: 
                # Store the disk results 
                self.disk_store[out.i] = out.de 
                # Add the difference in ball cardinality to the FreqDistribution
                self.distr.add(t, out.nnew) 
                # See if the counter changed
                counters_changed = counters_changed or out.de.changed 

            # Load disk_store to C 
            self.ld_c_disk()
            t+= 1 

def process_node(params: NodeProcessParams) -> NodeProcessOutput:
    # Skip if nothing changed last time 
    if not params.de.changed:
        return NodeProcessOutput(params.i, params.de,0)

    # Copy c[i] to a 
    a = params.c[params.i].copy()
    # Expand the ball and see if anything changed  
    ch = False 
    for w in params.ni: 
        ch |= a.union_ip(params.c[w])
         
    # Get estimated cardinality of the ball 
    Ea = a.getE() 
    
    # Create datatype for memoized values 
    de2 = DiskEntry(a, Ea, changed=ch)
    # Retunr the datatype
    return NodeProcessOutput(params.i, de2, Ea - params.de.Ea)


            
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
            
            


    

