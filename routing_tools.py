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