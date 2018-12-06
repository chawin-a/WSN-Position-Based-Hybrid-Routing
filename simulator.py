# import wsnsimpy.wsnsimpy as wsp
import wsnsimpy.wsnsimpy_tk as wsp
import random
from PhaseI import *
from PhaseII import *
from generate_data import *
import csv
import sys

def runsim(seed, tx_range, num_data):
    random.seed(seed)
    sim = wsp.Simulator(timescale=0, until=50, terrain_size=(700, 700), visual=False)
    # sim = wsp.Simulator(timescale=0.1, until=50, terrain_size=(700, 700), visual=True)
    # place 100 nodes on 10x10 grid space
    nodes = generate_node(seed)
    for px, py in nodes:
        sim.add_node(PhaseI, (px, py))
    # sim.master = master
    sim.master = random.randint(0, 99)
    sim.tx_range = tx_range
    sim.run()

    sim2 = wsp.Simulator(timescale=0, until=50, terrain_size=(700, 700), visual=False)
    
    # copy data from PhaseI to PhaseII
    for n in sim.nodes:
        sim2.add_node(PhaseII, n.pos)
    for i in range(len(sim.nodes)):
        if sim2.nodes[i].id != sim.nodes[i].my_master:
            sim2.nodes[i].my_master = sim.nodes[i].my_master
            sim2.nodes[i].prev = sim.nodes[i].prev
        else:
            sim2.nodes[i].my_master = sim.nodes[i].my_master
            sim2.nodes[i].P = sim.nodes[i].P
            sim2.nodes[i].I = sim.nodes[i].I
            sim2.nodes[i].T = sim.nodes[i].T
        sim2.nodes[i].tx_range = sim.nodes[i].tx_range
    sim2.source, _ = generate_data(seed, num_data, 99)
    sim2.run()
    
    s1 = sum([n.send_packets for n in sim.nodes])
    s2 = sum([n.send_packets for n in sim2.nodes])
    return s1 + s2
    # return num_successes, num_tx, num_rx

# runsim(5, 60, 100, 23, 98)
seed = int(sys.argv[1])
with open(f"results_pbhra_{seed}.csv", "w") as out:
    writer = csv.writer(out)
    writer.writerow(['seed', 'range', 'num_data', 'packets'])
    for j in range(5):
        RANGE = 50 + (j+1) * 50
        for n in range(5, 101, 5):
            data = n
            print(f"RUNNING...{seed}, {RANGE}, {data}")
            packets = runsim(seed, RANGE, data)
            writer.writerow([seed, RANGE, data, packets])