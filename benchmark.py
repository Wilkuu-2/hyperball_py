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
    avg_peak_hyperball: int 
    avg_peak_bfs: int  
    accuracy: float 

@dataclass(slots=False)
class TimeBenchmark:
    avg_hyperball: float 
    avg_bfs: float  
    accuracy: float 
    
def hyperball_task(g,bits,parallel=True): 
    from hyperball import HyperBallDistances
    run_h = HyperBallDistances.run_parallel if parallel else  HyperBallDistances.run
    rets = [0.0]

    def run():
        h = HyperBallDistances(bits, g)
        run_h(h) 
        rets[0] += h.distr.avg()

    return run, rets 

def bfs_task(g, parallel=True):
    from bfs import BFS_DistanceDistrParallel, BFS_DistanceDistr
    rets = [0.0]
    run_dfs = BFS_DistanceDistrParallel if parallel else BFS_DistanceDistr 
    def run():
        d = run_dfs(g)
        rets[0] += d.avg()
    
    return run, rets  


def gen_graph(NNODES, M, SEED):
    print("--------------------------------------------------")
    print(f"Preferentia attachement graph: {NNODES} nodes, M={M}, SEED={SEED}")
    return networkx.barabasi_albert_graph(NNODES,M, seed=SEED)

def human_size(size, decimal_places=3):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024.0 or unit == 'PiB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}" #type: ignore


def profile_mem(g, iterations, no_bfs) -> MemoryBenchmark: 
    sum_bfs = 0 
    sum_hyperball = 0
    acc_total = 0 

    for _ in range(iterations):
        tracemalloc.reset_peak()

        print(" ----------Mem:  HyperBall: ")
        f, ret = hyperball_task(g,8)
        f()
        hb_res = ret[0]
        print("RESULT: ", ret[0])
        
        m =  tracemalloc.get_traced_memory()[1]
        sum_hyperball += m;  
        
        print("Peak Mem:", human_size(m) )
        tracemalloc.reset_peak()

        print(" ----------Mem: BFS: ")
        f , ret = bfs_task(g)
        f()
        bfs_res = ret[0]
        print("RESULT: ", ret[0])

        m =  tracemalloc.get_traced_memory()[1]
        sum_bfs += m
        print("Peak Mem:", human_size(m))

        acc = 100 - (abs(bfs_res - hb_res) / bfs_res * 100.0)
        acc_total += acc 

        print(f" ------Mem ACCURACY = {acc}%" )
        tracemalloc.reset_peak()

    return MemoryBenchmark(sum_hyperball // iterations, sum_bfs // iterations, acc_total / iterations)
    
def profile_time(g, iterations,no_bfs ) -> TimeBenchmark: 
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
    
    file = "out.json" if args.file_out == '' else args.file_out 
    out_preamble = f"{{\"profile_type\": \"{args.bench_type}\", \"seed\": {args.seed}, \"frames\": \n{{"
    
    profile_fn = profile_time
    if args.bench_type == 'mem':
        tracemalloc.start()
        profile_fn = profile_mem 

    with open(file, 'w') as f:
        f.write(out_preamble)
        f.flush()
        for i in range(args.begin,args.end+1,args.increment):
            f.write(f"\"{i}\": ")
            frame = profile_fn(gen_graph(i, 5, args.seed),args.iterations,args.no_bfs)
            json.dump(frame, f, default=vars)
            if i + args.increment < args.end + 1:      
                f.write(",\n")
            f.flush()
        

        f.write("}}")

    if args.bench_type == 'mem':
        tracemalloc.stop() 



if __name__ == "__main__": 
    main()
