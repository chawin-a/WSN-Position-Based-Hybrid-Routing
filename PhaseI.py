import wsnsimpy.wsnsimpy_tk as wsp
import random
from routing_tools import *

class PhaseI(wsp.LayeredNode):
    
    def init(self):
        super().init()
        self.prev = None
        self.success_map = False
        self.my_master = -1
        self.tx_range = self.sim.tx_range
        self.count = 1
        self.is_center = False
        self.send_packets = 0
        # DEBUG
        self.logging = True

    def run(self):
        if self.id == self.sim.master:
            self.success_map = True
            self.my_master = self.id
            self.P = [[0 for x in range(5)] for y in range(100)]
            self.visited = [False for y in range(100)] 
            self.visited[self.id] = True
            self.P[self.id][0] = self.pos[0]
            self.P[self.id][1] = self.pos[1]
            yield self.timeout(1)
            self.send_map(self.id, False)
            self.scene.nodewidth(self.id, 3)
            self.scene.nodecolor(self.id, 1, 0, 0)
        else:
            self.success_map = False
            self.scene.nodecolor(self.id, .7, .7, .7)

    def on_receive(self, sender, data):
        msg = data["msg"]
        if msg == "map":
            master_id = data["master_id"]
            is_center = data["is_center"]
            if not self.success_map:
                self.scene.nodecolor(self.id, .4, .4, .4)
                self.success_map = True
                self.my_master = master_id
                self.prev = sender
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_map(master_id, False)
                # self.scene.nodewidth(self.id, 3)
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_up((self.id, self.pos))
                self.scene.nodecolor(self.id, 0, 0, .7)

            elif self.is_center != is_center:
                self.my_master = master_id
                self.prev = sender
                self.is_center = is_center
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_map(master_id, is_center)

        elif msg == "up":
            u_data = data["u_data"]
            if self.id != self.my_master:
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_up(u_data)
            else:
                if self.visited[u_data[0]]:
                    return
                self.visited[u_data[0]] = True
                self.P[u_data[0]][0] = u_data[1][0]
                self.P[u_data[0]][1] = u_data[1][1]
                self.count += 1
                if self.count == 100:
                    # Compute matrix I
                    self.create_I_matrix() # all-pair distance matrix
                    self.create_T_matrix() # sum of distance
                    new_master = self.T.index(min(self.T))
                    path = dijkstra(self.id, new_master, self.I, self.tx_range)[1:]
                    if len(path) > 0:
                        yield self.timeout(random.uniform(0.1, 0.5))
                        self.transfer_master(path, self.P, self.I, self.T)
                        self.P = None
                        self.I = None
                        self.T = None
                        self.count = 1
                        self.scene.nodecolor(self.id, 0, 0, .7)
                        self.scene.nodewidth(self.id, 1)
                    else:
                        self.is_center = True
                        yield self.timeout(random.uniform(0.1, 0.5))
                        self.send_map(self.id, True)

        elif msg == "transfer_m":
            P = data["P"]
            I = data["I"]
            T = data["T"]
            path = data["path"]
            if len(path) > 0:
                yield self.timeout(random.uniform(0.1, 0.5))
                self.transfer_master(path, P, I, T)
            else:
                self.my_master = self.id
                self.P = P
                self.I = I
                self.T = T
                self.scene.nodecolor(self.id, 1, 0, 0)
                self.scene.nodewidth(self.id, 3)
                self.is_center = True
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_map(self.id, True)
                    
    def transfer_master(self, path, P, I, T):
        data = {
            "msg": "transfer_m",
            "path": path[1:],
            "P": P,
            "I": I,
            "T": T
        }
        self.send_packets += 1
        self.send(path[0], data=data)

    def create_I_matrix(self):
        self.I = [[0 for x in range(100)] for y in range(100)]
        for i in range(100):
            for j in range(i+1,100):
                p1 = (self.P[i][0], self.P[i][1])
                p2 = (self.P[j][0], self.P[j][1])
                dist = distance(p1, p2)
                self.I[i][j] = self.I[j][i] = dist

    def create_T_matrix(self):
        self.T = [sum(self.I[y][x] for y in range(100)) for x in range(100)]

    def send_map(self, master_id, is_center):
        data = {
            "msg": "map",
            "master_id": master_id,
            "is_center": is_center
        }
        self.send_packets += 1
        self.send(wsp.BROADCAST_ADDR, data=data)

    def send_up(self, u_data):
        data = {
            "msg": "up",
            "u_data": u_data
        }
        self.send_packets += 1
        self.send(self.prev, data=data)
