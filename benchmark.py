import argparse
import json 
import tracemalloc 
import timeit 
import networkx 
from random import randint
from dataclasses import dataclass 
import os

@dataclass(slots=False)
class MemoryBenchmark:
    """Datatype to save memory bencmarks"""
    avg_peak_hyperball: int 
    avg_peak_bfs: int  
    accuracy: float 

@dataclass(slots=False)
class TimeBenchmark:
    """Datatype to save time bencmarks"""
    avg_hyperball: float 
    avg_bfs: float  
    accuracy: float 
    
def hyperball_task(g,bits,parallel=True): 
    """Creates a function that executes HyperBall on a given graph with given precision"""
    from hyperball import HyperBallDistances
    # Chooses between parallelized and non-parallelized function 
    run_h = HyperBallDistances.run_parallel if parallel else  HyperBallDistances.run 
    rets = [0.0] # stores return value 

    def run():
        h = HyperBallDistances(bits, g)
        run_h(h) 
        rets[0] += h.distr.avg()

    return run, rets 

def bfs_task(g, parallel=True):
    """Creates a function that executes BFS on a given graph"""
    from bfs import BFS_DistanceDistrParallel, BFS_DistanceDistr
    rets = [0.0] # Stores return value 
    # Chooses between parallelized and non-parallelized function 
    run_dfs = BFS_DistanceDistrParallel if parallel else BFS_DistanceDistr 

    def run():
        d = run_dfs(g)
        rets[0] += d.avg()
    
    return run, rets  


def gen_graph(NNODES, M, SEED):
    """Generates a Preferential attachement graph with the given parameters"""

    print("--------------------------------------------------")
    print(f"Preferential attachement graph: {NNODES} nodes, M={M}, SEED={SEED}")
    return networkx.barabasi_albert_graph(NNODES,M, seed=SEED)

def human_size(size, decimal_places=3):
    """
    Converts given byte counts to human readable size
        Source: https://stackoverflow.com/questions/1094841/get-human-readable-version-of-file-size
    """
    
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024.0 or unit == 'PiB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}" #type: ignore

def profile_mem(g, iterations, no_bfs) -> MemoryBenchmark: 
    """
    Profiles memory for a given graph 
        Runs 4x slower and only works on non-parallelized versions of the function 
    """
    sum_bfs = 0 
    sum_hyperball = 0
    acc_total = 0 

    for _ in range(iterations):

        print(" ----------Mem:  HyperBall: ")
        f, ret = hyperball_task(g,8,parallel=False)
        
        # record hyperball execution
        tracemalloc.reset_peak()
        f()
        m =  tracemalloc.get_traced_memory()[1]
        tracemalloc.reset_peak()
        # end recording 

        sum_hyperball += m;  
        hb_res = ret[0]
        print("RESULT: ", hb_res)
        print("Peak Mem:", human_size(m) )

        acc = 100
        # Bfs is optional
        if not no_bfs:
            print(" ----------Mem: BFS: ")
            # record bfs execution
            tracemalloc.reset_peak()
            f , ret = bfs_task(g,parallel=False)
            f()
            m =  tracemalloc.get_traced_memory()[1]
            tracemalloc.reset_peak()
            # end_recording 

            bfs_res = ret[0]
            print("RESULT: ", bfs_res)
            print("Peak Mem:", human_size(m))
            sum_bfs += m

            acc = 100 - (abs(bfs_res - hb_res) / bfs_res * 100.0)
        acc_total += acc 

        print(f" ------Mem ACCURACY = {acc}%" )

    return MemoryBenchmark(sum_hyperball // iterations, sum_bfs // iterations, acc_total / iterations)
    
def profile_time(g, iterations,no_bfs ) -> TimeBenchmark: 
    """Profiles time for a given graph"""
    print(" ----------T: HyperBall: ")
    f, ret = hyperball_task(g,8)
    t = timeit.Timer(f)

    avg_hyperball = t.timeit(iterations)
    hb_res = ret[0] / iterations 
    print("RESULT: ", hb_res)
    print(f"Time: {avg_hyperball}")
    
    print(" ----------T: BFS: ")
    f , ret = bfs_task(g)
    t = timeit.Timer(f)

    acc = 100 
    avg_bfs = 0.0
    
    # Bfs is optional
    if not no_bfs:
        avg_bfs = t.timeit(iterations)
        bfs_res = ret[0] / iterations 
        print("RESULT: ", bfs_res)
        print(f"Time: {avg_bfs}")
        acc = 100 - (abs(bfs_res - hb_res) / bfs_res * 100.0)
        print(f" -------- ACCURACY = {acc}%" )
    
    
    return TimeBenchmark(avg_hyperball, avg_bfs, acc)

def main(): 
    ap = argparse.ArgumentParser()
    ap.add_argument("bench_type", choices=['mem','time'])
    ap.add_argument("file_out", default='')
    ap.add_argument("-b", "--begin", default=200, type=int)
    ap.add_argument("-i", "--increment", default=400, type=int)
    ap.add_argument("-e", "--end", default=2200, type=int)
    ap.add_argument("-s", "--seed", default=randint(1001,9999), type=int)
    ap.add_argument("-n", "--iterations", default=1, type=int)
    ap.add_argument("-k", "--no_bfs", action="store_true",)

    args = ap.parse_args()
    
    

    #Profiling time is the default, set profile_fn to the profile_time function 
    profile_fn = profile_time
    
    # Start tracemalloc and change the profile function when the type is mem
    if args.bench_type == 'mem':
        tracemalloc.start()
        profile_fn = profile_mem 
    
    # Start writing to file by dumping the parameters
    file = "out.json" if args.file_out == '' else args.file_out 
    out_preamble = f"{{\"profile_type\": \"{args.bench_type}\", \"seed\": {args.seed}, \"frames\": \n{{"

    with open(file, 'w') as f:
        # Preambe 
        f.write(out_preamble)
        f.flush()

        # For each amount of nodes, we write to file, so we keep the data in a semi OK file when we fail 
        for i in range(args.begin,args.end+1,args.increment):

            #Write the node amount as key
            f.write(f"\"{i}\": ")
            
            #Write the benchmark frame as value 
            frame = profile_fn(gen_graph(i, 5, args.seed),args.iterations,args.no_bfs)
            json.dump(frame, f, default=vars)

            #Add a comma and a new line if this is not the last iteration of the for loop 
            if i + args.increment < args.end + 1:      
                f.write(",\n")
            f.flush()

        # Terminate the json objects 
        f.write("}}")
    
    # Stop tracemalloc if needed
    if args.bench_type == 'mem':
        tracemalloc.stop() 



if __name__ == "__main__": 
    main()
