import wsnsimpy.wsnsimpy_tk as wsp
import random
from routing_tools import *

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
        if self.id == self.sim.source:
            if self.id != self.my_master:
                yield self.timeout(random.uniform(0.1, 0.5))
                self.send_request_path(self.id, self.sim.destination)
            else:
                path = dijkstra(self.id, self.sim.destination, self.I, self.tx_range)
                for i in range(int(random.uniform(5, 10))):
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
                for i in range(int(random.uniform(5, 10))):
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