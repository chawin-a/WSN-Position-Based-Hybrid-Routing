# import wsnsimpy.wsnsimpy as wsp
import wsnsimpy.wsnsimpy_tk as wsp
import random
from PhaseI import *
from PhaseII import *

def runsim(seed, tx_range):
    random.seed(seed)
    sim = wsp.Simulator(timescale=0, until=50, terrain_size=(700, 700), visual=False)
    # sim = wsp.Simulator(timescale=0.1, until=50, terrain_size=(700, 700), visual=True)
    # place 100 nodes on 10x10 grid space
    for x in range(10):
        for y in range(10):
            px = 50 + x*60 + random.uniform(-20, 20)
            py = 50 + y*60 + random.uniform(-20, 20)
            sim.add_node(PhaseI, (px, py))
    # sim.master = master
    sim.master = int(random.uniform(0, 99))
    sim.tx_range = tx_range
    source = int(random.uniform(0, 29))
    destination = int(random.uniform(70, 99))
    sim.run()

    sim2 = wsp.Simulator(timescale=0, until=50, terrain_size=(700, 700), visual=True)
    
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
    sim2.source = source
    sim2.destination = destination
    sim2.run()
    
    # return num_successes, num_tx, num_rx

# runsim(5, 60, 100, 23, 98)
# for i in range(20):
#     print(i)
#     for j in range(5):
#         runsim(i, 50 + (j+1) * 50)
runsim(9, 300)