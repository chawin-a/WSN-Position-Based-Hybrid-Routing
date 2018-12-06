import random

def generate_data(seed, n, lim):
    data = []
    visited = dict()
    random.seed(seed)
    while len(data) < n:
        u = random.randint(0, lim)
        v = random.randint(0, lim)
        if u == v:
            continue
        if visited.get((u, v)) != None:
            continue
        data.append((u, v))

    ret = dict()
    for u, v in data:
        if ret.get(u) == None:
            ret[u] = []
        ret[u].append(v)
    return ret, data

def generate_node(seed):
    random.seed(seed)
    ret = []
    for x in range(10):
        for y in range(10):
            px = 50 + x*60 + random.uniform(-20, 20)
            py = 50 + y*60 + random.uniform(-20, 20)
            ret.append((px, py))
    return ret