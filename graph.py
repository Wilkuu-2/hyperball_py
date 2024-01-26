
import argparse
import json
from matplotlib import pyplot as plt 

def parse_opt_float(f) -> float | None: 
    """Filters out floats of value 0"""
    return None if f == 0.0 else f

def filter_acc(f) -> float | None: 
    """Filters out 100% or 0% accuracies"""
    return None if f == 100.0 or f == 0.0 else f 

def main(): 
    # Get args 
    ap = argparse.ArgumentParser()
    ap.add_argument("file_in")
    ap.add_argument("file_out", default='graph.jpg')
    ap.add_argument("-n", "--no-show", action="store_true")
    args = ap.parse_args()

    data = None 
    with open(args.file_in,'r') as infile: 
        data = json.load(infile)


    # Get type of benchmark 
    dtype = data["profile_type"]

    # Set the json keys for data 
    dkeys = ['avg_peak_hyperball','avg_peak_bfs'] if dtype == 'mem' else ['avg_hyperball','avg_bfs']

    # Get the values in form of 3 arrays
    N, hyperball_score, bfs_score, acc = zip(
            *[(int(k),
               parse_opt_float(v[dkeys[0]]),
               parse_opt_float(v[dkeys[1]]),
               filter_acc(v['accuracy']))
              for (k,v) in data['frames'].items()])

    # Get the two subplots 
    f, (a,b) = plt.subplots(2,1)

    # Plot out the comparison 
    a.plot(N,hyperball_score, label="Hyperball")
    a.plot(N,bfs_score, label="BFS") 

    # Plot out the accuracy 
    b.plot(N,acc, label="Accuracy of Hyperball vs BFS")

    # Gets the titles right 
    b.set_title("Accuracy")
    if dtype == 'mem':
        a.set_title("Peak memory usage of Hyperball vs BFS")
        a.set_ylabel("Peak memory usage (B)")
    else: # dtype == 'time' 
        a.set_title("Execution time of Hyperball vs BFS")
        a.set_ylabel("Execution time (s)")

    # Legend 
    a.legend()

    # Save the figure
    f.savefig(args.file_out)
    print(f"Saved figure at: {args.file_out}")

    if not args.no_show:
        plt.show()

if __name__ ==  "__main__":
    main()

        

