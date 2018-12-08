import wsnsimpy.wsnsimpy_tk as wsp
import random
from PhaseI import *
from routing_tools import *
from generate_data import *

class PhaseII(wsp.LayeredNode):
    def init(self):
        super().init()
        self.send_packets = 0
        if self.id == self.my_master:
            self.scene.nodewidth(self.id, 3)
            self.scene.nodecolor(self.id, 1, 0, 0) 
        # DEBUG
        self.logging = True

    def run(self):
        if self.sim.source.get(self.id) != None:
            for dest in self.sim.source[self.id]:
                if self.id != self.my_master:
                    yield self.timeout(random.uniform(0.1, 0.5))
                    self.send_request_path(self.id, dest)
                else:
                    path = dijkstra(self.id, dest, self.I, self.tx_range)
                    # for i in range(int(random.uniform(5, 10))):
                    for i in range(self.sim.ROUND):
                        yield self.timeout(random.uniform(0.1, 0.5))
                        self.send_msg(path[1:], "hello")

    def on_receive(self, sender, data):
        msg = data["msg"]
        if msg == "req_path":
            s = data["source"]
            d = data["destination"]
            if self.id != self.my_master:
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_request_path(s, d)
            else:
                yield self.timeout(random.uniform(0.1, 0.5))
                path = dijkstra(s, d, self.I, self.tx_range)
                path_to_source = dijkstra(self.id, s, self.I, self.tx_range)[1:]
                self.send_path(path, path_to_source)

        elif msg == "res_path":
            path_to_source = data["path_to_source"]
            path = data["path"]
            if len(path_to_source) > 0:
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_path(path, path_to_source)
            else:
                # for i in range(int(random.uniform(5, 10))):
                for i in range(self.sim.ROUND):
                    yield self.timeout(random.uniform(0.1, 0.5))
                    self.send_msg(path[1:], "hello")

        elif msg == "send_msg":
            path = data["path"]
            message = data["message"]
            if len(path) > 0:
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_msg(path, message)

    def send_request_path(self, source, destination):
        data = {
            "msg": "req_path",
            "source": source,
            "destination": destination
        }
        self.send_packets += 1
        self.send(self.prev, data=data)
    
    def send_path(self, path, path_to_source):
        data = {
            "msg": "res_path",
            "path": path,
            "path_to_source": path_to_source[1:]
        }
        self.send_packets += 1
        self.send(path_to_source[0], data=data)

    def send_msg(self, path, message):
        data = {
            "msg": "send_msg",
            "path": path[1:],
            "message": message
        }
        self.send_packets += 1
        self.send(path[0], data=data)

def main():
    seed = 123
    tx_range = 100
    num_data = 1
    ROUND = 1
    random.seed(seed)
    sim = wsp.Simulator(timescale=0, until=50, terrain_size=(700, 700), visual=False)
    nodes = generate_node(seed)
    for px, py in nodes:
        sim.add_node(PhaseI, (px, py))
    # sim.master = master
    sim.master = random.randint(0, 99)
    sim.tx_range = tx_range
    sim.run()

    sim2 = wsp.Simulator(timescale=3, until=50, terrain_size=(700, 700), visual=True)
    
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
    sim2.source, _ = generate_data(4, num_data, 99)
    sim2.ROUND = ROUND
    sim2.run()

if __name__ == '__main__':
    main()