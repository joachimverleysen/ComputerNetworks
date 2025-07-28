class GraphTableEntry:
    def __init__(self, node, distance, parent):
        self.node = node
        self.distance = distance
        self.parent = parent

class Graph:
    def __init__(self, nodes):
        self.nodes = nodes
        self.edges = []
        self.table = []

    def connect(self, start, end, cost):
        self.edges.append((Edge(start, end, cost)))

    def addTableEntry(self, node, distance, parent):
        self.table.append(GraphTableEntry(node, distance, parent))


class Edge:
    def __init__(self, start, end, cost):
        self.start = start
        self.end = end
        self.cost = cost

if __name__ == "__main__":
    graph = Graph(["A", "B", "C", "D", "E", "F"])
    graph.connect("A", "B", 5)
    graph.connect("A", "C", 2)
    graph.connect("B", "C", 1)
    graph.connect("B", "D", 4)
    graph.connect("B", "E", 2)
    graph.connect("C", "E", 7)
    graph.connect("E", "F", 1)
    graph.connect("D", "E", 6)
    graph.connect("D", "F", 3)

