
import argparse
import json
from matplotlib import pyplot as plt 

def parse_opt_float(f) -> float | None: 
    return None if f == 0.0 else f

def filter_acc(f) -> float | None: 
    return None if f == 100.0 or f == 0.0 else f 

def main(): 
    ap = argparse.ArgumentParser()
    ap.add_argument("file_in")
    ap.add_argument("file_out", default='graph.jpg')
    

    args = ap.parse_args()

    data = None 
    with open(args.file_in,'r') as infile: 
        data = json.load(infile)


    dtype = data["profile_type"]
    dkeys = ['avg_peak_hyperball','avg_peak_bfs'] if dtype == 'mem' else ['avg_hyperball','avg_bfs']
    N, hyperball_score, bfs_score, acc = zip(
            *[(int(k),
               parse_opt_float(v[dkeys[0]]),
               parse_opt_float(v[dkeys[1]]),
               filter_acc(v['accuracy']))
              for (k,v) in data['frames'].items()])

    f, (a,b) = plt.subplots(2,1)
    a.plot(N,hyperball_score, label="Hyperball")
    a.plot(N,bfs_score, label="BFS") 
    b.plot(N,acc, label="Accuracy of Hyperball vs BFS")

    if dtype == 'mem':
        a.set_title("Peak memory usage of Hyperball vs BFS")
        a.set_ylabel("Peak memory usage (B)")
    else: # dtype == 'time' 
        a.set_title("Execution time of Hyperball vs BFS")
        a.set_ylabel("Execution time (s)")

    b.set_title("Accuracy")
    

    a.legend()
    plt.show()


if __name__ ==  "__main__":
    main()

        

