from typing import Set
import networkx 
from common import FreqDistribution 
from collections import deque
import multiprocessing 

def BFS_GetDDSingleTuple(g) ->FreqDistribution:
    return BFS_GetDDSingle(g[0], g[1])

def BFS_GetDDSingle(G: networkx.Graph, s: str) -> FreqDistribution: 
    c = FreqDistribution(32) 
    visited = set()
    queue = deque([(s, int(0))])
    while len(queue) > 0: 
        v, d0 = queue.pop() 
        if v not in visited: 
            visited.add(v)
            c.add(d0)
            nv: Set[str] = (set(G[v]) - visited)
            queue.extendleft(map(lambda x: (x, d0+1), nv))
        
    return c 

def BFS_DistanceDistr(G: networkx.Graph) -> FreqDistribution:
    c = FreqDistribution(32)
    for n in G.nodes(): 
        c.merge_ip(BFS_GetDDSingle(G, n))

    c.arr[0] = 0 
    c.half()
    return c

def BFS_DistanceDistrParallel(G: networkx.Graph) -> FreqDistribution: 
    pool = multiprocessing.Pool()
    distrs = pool.map(BFS_GetDDSingleTuple,
                      [(G,n) for n in list(G.nodes())])
    
    c = FreqDistribution(32)
    for d in distrs:
        c.merge_ip(d)

    return c






def test(): 
    print("GNP graph: The answer should be around 3")
    g = networkx.fast_gnp_random_graph(2000,0.32, seed=4209)
    d = BFS_DistanceDistrParallel(g)
    print(d.arr)
    print(d.count())
    print(d.avg())

    print("Complete graph: the average should be 1 exactly") 
    g = networkx.complete_graph(50) 
    d = BFS_DistanceDistr(g)
    print(d.arr)
    print(d.count())
    print(d.avg())

if __name__ == "__main__":
    test()
        



    



