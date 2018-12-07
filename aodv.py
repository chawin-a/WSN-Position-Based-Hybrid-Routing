import random
import wsnsimpy.wsnsimpy_tk as wsp
from generate_data import *
import csv
import sys

###########################################################
def delay():
    return random.uniform(.2,.8)

###########################################################
class MyNode(wsp.Node):
    # tx_range = 100

    ###################
    def init(self):
        super().init()
        self.prev = None
        self.send_packets = 0
        self.logging = False

    ###################
    def run(self):
        if self.id is self.sim.SOURCE:
            self.scene.nodecolor(self.id,0,0,1)
            self.scene.nodewidth(self.id,2)
            yield self.timeout(1)
            self.send_rreq(self.id)
        elif self.id is self.sim.DEST:
            self.scene.nodecolor(self.id,1,0,0)
            self.scene.nodewidth(self.id,2)
        else:
            self.scene.nodecolor(self.id,.7,.7,.7)

    ###################
    def send_rreq(self,src):
        self.send_packets += 1
        self.send(wsp.BROADCAST_ADDR, msg='rreq', src=src)

    ###################
    def send_rreply(self,src):
        if self.id is not self.sim.DEST:
            self.scene.nodecolor(self.id,0,.7,0)
            self.scene.nodewidth(self.id,2)
        self.send_packets += 1
        self.send(self.prev, msg='rreply', src=src)

    ###################
    def start_send_data(self):
        self.scene.clearlinks()
        for i in range(self.sim.ROUND):
            yield self.timeout(1)
            self.log(f"Send data to {self.sim.DEST}")
            self.send_data(self.id)

    ###################
    def send_data(self,src):
        self.log(f"Forward data via {self.next}")
        self.send_packets += 1
        self.send(self.next, msg='data', src=src)

    ###################
    def on_receive(self, sender, msg, src, **kwargs):

        if msg == 'rreq':
            if self.prev is not None: return
            self.prev = sender
            self.scene.addlink(sender,self.id,"parent")
            if self.id is self.sim.DEST:
                self.log(f"Receive RREQ from {src}")
                yield self.timeout(5)
                self.log(f"Send RREP to {src}")
                self.send_rreply(self.id)
            else:
                yield self.timeout(delay())
                self.send_rreq(src)

        elif msg == 'rreply':
            self.next = sender
            if self.id is self.sim.SOURCE:
                self.log(f"Receive RREP from {src}")
                yield self.timeout(5)
                self.log("Start sending data")
                self.start_process(self.start_send_data())
            else:
                yield self.timeout(.2)
                self.send_rreply(src)

        elif msg == 'data':
            if self.id is not self.sim.DEST:
                yield self.timeout(.2)
                self.send_data(src,**kwargs)
            else:
                self.log(f"Got data from {src}")

###########################################################
def runsim(seed, u, v, tx_range, ROUND):
    random.seed(seed)
    sim = wsp.Simulator(
            until=100,
            timescale=0,
            visual=False,
            terrain_size=(700,700),
            title="AODV Demo")

    # define a line style for parent links
    sim.scene.linestyle("parent", color=(0,.8,0), arrow="tail", width=2)
    sim.SOURCE = u
    sim.DEST = v
    sim.ROUND = ROUND
    # place nodes over 100x100 grids
    nodes = generate_node(seed)
    for px, py in nodes:
        node = sim.add_node(MyNode, (px,py))
        node.tx_range = tx_range
        node.logging = True

    # start the simulation
    sim.run()

    packets = sum([n.send_packets for n in sim.nodes])
    return packets

# runsim(0, 1, 99, 300)

seed = int(sys.argv[1])
with open(f"results_aodv_{seed}.csv", "w") as out:
    writer = csv.writer(out)
    writer.writerow(['seed', 'range', 'num_data', 'packets'])
    for i in range(5, 101, 5):
        n = i
        _, data = generate_data(seed, n, 99)
        for j in range(5):
            RANGE = 50 + (j+1) * 50
            print(f"RUNNING...{seed}, {RANGE}, {n}")
            packets = 0
            for u, v in data:
                packets += runsim(seed, u, v, RANGE, 1)
            writer.writerow([seed, RANGE, n, packets])