# import wsnsimpy.wsnsimpy as wsp
import wsnsimpy.wsnsimpy_tk as wsp
import random
import math
import queue

def distance(p1, p2):
    return (((p1[0]-p2[0]) ** 2) + ((p1[1]-p2[1]) ** 2)) ** 0.5

def dijkstra(s, d, matrix, tx_range):
    q = queue.PriorityQueue()
    q.put((0, s, [s]))
    visited = [False for x in range(100)]
    path = None 
    while not q.empty():
        dist, u, p = q.get()
        if visited[u]:
            continue
        visited[u] = True
        if u == d:
            path = p 
            break
        for v in range(100):
            if matrix[u][v] <= tx_range:
                q.put((dist + matrix[u][v], v, p + [v]))
    return path

class PhaseI(wsp.LayeredNode):
    
    def init(self):
        super().init()
        self.prev = None
        self.success_map = False
        self.my_master = -1
        self.tx_range = self.sim.tx_range
        self.count = 1
        self.is_center = False
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

    def send_request_path(self, s, d):
        data = {
            "msg": "req_path",
            "source": s,
            "destination": d
        }
        self.send(self.prev, data=data)
    
    def send_path(self, path, path_to_source):
        data = {
            "msg": "res_path",
            "path": path,
            "path_to_source": path_to_source[1:]
        }
        self.send(path_to_source[0], data=data)

    def send_msg(self, path, message):
        data = {
            "msg": "send_msg",
            "path": path[1:],
            "message": message
        }
        self.send(path[0], data=data)

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

                if self.id == self.sim.source:
                    if self.id != self.my_master:
                        yield self.timeout(random.uniform(0.1, 0.5))
                        self.send_request_path(self.id, self.sim.destination)
                    else:
                        path = dijkstra(self.id, self.sim.destination, self.I, self.tx_range)
                        for i in range(int(random.uniform(5, 10))):
                            yield self.timeout(random.uniform(0.1, 0.5))
                            self.send_msg(path[1:], "hello")
        
        elif msg == "req_path":
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
                for i in range(int(random.uniform(5, 10))):
                    yield self.timeout(random.uniform(0.1, 0.5))
                    self.send_msg(path[1:], "hello")

        elif msg == "send_msg":
            path = data["path"]
            message = data["message"]
            if len(path) > 0:
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_msg(path, message)
            else:
                pass

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
        self.send(wsp.BROADCAST_ADDR, data=data)

    def send_up(self, u_data):
        data = {
            "msg": "up",
            "u_data": u_data
        }
        self.send(self.prev, data=data)

class PhaseII(wsp.LayeredNode):
    pass
        
def runsim(seed, tx_range):
    random.seed(seed)
    # sim = wsp.Simulator(timescale=0, until=50, terrain_size=(700, 700), visual=False)
    sim = wsp.Simulator(timescale=0.1, until=50, terrain_size=(700, 700), visual=True)
    # place 100 nodes on 10x10 grid space
    for x in range(10):
        for y in range(10):
            px = 50 + x*60 + random.uniform(-20, 20)
            py = 50 + y*60 + random.uniform(-20, 20)
            sim.add_node(PhaseI, (px, py))
    # sim.master = master
    sim.master = int(random.uniform(0, 99))
    sim.tx_range = tx_range
    sim.source = int(random.uniform(0, 29))
    sim.destination = int(random.uniform(70, 99))
    sim.run()

    sim2 = wsp.Simulator(timescale=0, until=50, terrain_size=(700, 700), visual=False)
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
    sim2.run()
    
    # return num_successes, num_tx, num_rx

# runsim(5, 60, 100, 23, 98)
# for i in range(20):
#     print(i)
#     for j in range(5):
#         runsim(i, 50 + (j+1) * 50)
runsim(9, 300)