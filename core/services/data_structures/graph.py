import json

try:
    from .utils import AdaptableHeapPriorityQueue
except ImportError:

    from utils import AdaptableHeapPriorityQueue


class Graph:
    """使用邻接矩阵实现图结构"""

    # ------------------------- nested Vertex class -------------------------
    class Vertex:
        """顶点集合"""
        __slots__ = '_element'

        def __init__(self, x):
            """Use Graph's insert_vertex(x). 创建点"""
            self._element = x

        def element(self):
            """返回顶点存储的值"""
            return self._element

        def __hash__(self):  # hash 函数
            return hash(id(self))

        def __repr__(self):
            return f"Vertex('element={self._element}')"

    # ------------------------- nested Edge class -------------------------
    class Edge:
        """边集合"""
        __slots__ = '_origin', '_destination', '_element'

        def __init__(self, u, v, x):
            """Use Graph's insert_edge(u,v,x). 创建边"""
            self._origin = u
            self._destination = v
            self._element = x

        def endpoints(self):
            """返回 (u, v): u 为出射点, v 为入射点"""
            return (self._origin, self._destination)

        def opposite(self, v):
            """返回在当前边上 v 的邻接点"""
            return self._destination if v is self._origin else self._origin

        def element(self):
            """返回边上的数据, 例如权重"""
            return self._element

        def __hash__(self):  # hash 函数
            """对边哈希, 方便后面二级结构 I(v) 以字典形式存储"""
            return hash((self._origin, self._destination))

        def __repr__(self):
            return f"Edge('weight={self._element}, from={self._origin.element()}', to='{self._destination.element()}')"

    # ------------------------- Graph methods -------------------------
    def __init__(self, directed=False):
        """
        初始化一个图, 默认为无向图
        :param directed: True 则为有向图
        """
        self._outgoing = {}  # 出射点集

        # 有向图时入射点集合为新, 否则指向出射点集
        self._incoming = {} if directed else self._outgoing

    def is_directed(self):
        """判断是否有方向"""
        return self._incoming is not self._outgoing

    def insert_vertex(self, x=None):
        """插入点, 返回点 Vertex 类"""
        v = self.Vertex(x)  # 创建新点, 值为 x
        self._outgoing[v] = {}  # 放入点集, 此时无边, 故为空

        if self.is_directed():
            self._incoming[v] = {}  # 如果有方向, 则入射点集也要加入
        return v

    def insert_edge(self, u, v, x=None):
        """插入边, 注意, 需要 u v 均为点 Vertex 类"""
        e = self.Edge(u, v, x)  # 从 u 到 v, 值为 x
        self._outgoing[u][v] = e  # 将边放入二级结构 I(u)
        self._incoming[v][u] = e  # 将边放入二级结构 I(v)
        return e

    def vertex_count(self):
        """总点数"""
        return len(self._outgoing)

    def vertices(self):
        """返回点的迭代器"""
        return self._outgoing.keys()

    def edge_count(self):
        """总边数"""
        # 总度数
        total = sum(len(self._outgoing[v]) for v in self._outgoing)

        # 无向图, 度求和要除以 2 . 有向图则不用
        return total if self.is_directed() else total // 2

    def edges(self):
        """返回图的所有边的集合 (已去重)"""
        result = set()  # 存储边集合, 防止重复
        for secondary_map in self._outgoing.values():
            result.update(secondary_map.values())  # 加入新边
        return result

    def get_edge(self, u, v):
        """返回点 u 到点 v 的边, 不相邻则为 None"""
        # 直接使用字典的 get() 方法, 没有则为 None
        return self._outgoing[u].get(v)

    def degree(self, v, outgoing=True):
        """
        返回顶点 v 的度, 默认为出度
        :param v: 顶点 Vertex 类
        :param outgoing: False 则返回入度
        :return: 顶点 v 的度
        """
        adj = self._outgoing if outgoing else self._incoming
        return len(adj[v])

    def incident_edges(self, v, outgoing=True):
        """
        以迭代器的形式返回顶点 v 的边, 默认为出射边
        :param v: 顶点 Vertex 类
        :param outgoing: False 则返回入射边
        :return: 从顶点 v 出射的边 (入射 v 的边)
        """
        adj = self._outgoing if outgoing else self._incoming
        for edge in adj[v].values():
            yield edge

    def neighbors(self, v, outgoing=True):
        adj = self._outgoing if outgoing else self._incoming
        return list(adj[v])

    def remove_edge(self, u, v):
        """
        删除顶点 u 到顶点 v 的边
        :param u: 边的起点
        :param v: 边的终点
        :return: 被删除边的元素
        """
        if u not in self._outgoing or v not in self._outgoing[u]:
            raise ValueError("Edge not in graph")

        e = self.get_edge(u, v)
        del self._outgoing[u][v]
        del self._incoming[v][u]

        return e.element()

    def remove_vertex(self, v):
        """
        删除顶点 v 及其所有关联边
        :param v: 要删除的顶点
        :return: 被删除顶点的元素
        """
        if v not in self._outgoing:
            raise ValueError("Vertex not in graph")

        # 首先删除所有与 v 关联的边
        neighbors = list(self._outgoing[v].keys())  # 所有邻接顶点

        # 对于无向图, 需要避免重复删除
        if self.is_directed():
            # 有向图: 删除所有出边和入边
            for u in neighbors:
                del self._incoming[u][v]  # 删除入边
            for w in self._incoming[v]:
                del self._outgoing[w][v]  # 删除出边
        else:
            # 无向图: 只需要删除一次
            for u in neighbors:
                del self._outgoing[u][v]

        # 删除顶点本身
        del self._outgoing[v]
        if self.is_directed():  # 有向
            del self._incoming[v]

        return v.element()

    def update_vertex(self, u, x):
        """更新点的值"""
        if u not in self._outgoing:
            raise ValueError("Vertex not in graph")
        old = u.element()
        u._element = x
        return old

    def update_edge(self, u, v, weight):
        """更新边的值"""
        e = self.get_edge(u, v)
        if e is None:
            raise ValueError("Edge not in graph")
        old = e.element()
        e._element = weight
        return old

    # ------------------------- Save and load graph into / from JSON -------------------------
    def save_to_json(self, filename):
        """保存为 json 格式, 邻接表的形式"""
        data = {
            "directed": self.is_directed(),
            "vertices": [v.element() for v in self.vertices()],
            "edges": []
        }

        # 使用集合, 去除重复边
        edge_set = set()

        for e in self.edges():
            u, v = e.endpoints()  # 取每一条边的端点

            # 对于无向图, 确保每条边只存储一次
            if (v, u) not in edge_set:
                edge_set.add((u, v))

                data["edges"].append({
                    "u": u.element(),
                    "v": v.element(),
                    "weight": e.element()
                })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_from_json(self, filename):
        """
        从 json 文件加载图, 返回定位器和当前最大的 uid , 若读取失败返回 False
        :param filename: 文件路径
        :return: ({v.element(): Graph.Vertex, ...}, max_uid) or False
        """
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return False
            data = json.loads(content)

        # 插入顶点并建立元素到顶点的映射
        # {v.element(): Graph.Vertex}
        if data["vertices"]:
            max_uid = max(data["vertices"])  # 此处不是本项目重点, 直接使用 python 的 max 函数
        else:
            max_uid = 0
        vertex_map = {v_elem: self.insert_vertex(v_elem) for v_elem in data["vertices"]}

        # 添加边
        # "edges": [{"u": u.element(), "v": u.element(), "weight": e.element()}, ...]
        for edge_data in data["edges"]:
            u = vertex_map[edge_data["u"]]
            v = vertex_map[edge_data["v"]]
            self.insert_edge(u, v, edge_data["weight"])

        return vertex_map, max_uid  # 返回 (定位器, max_uid)


# ==================== 广度优先搜索 ====================
def BFS(g: Graph, s: Graph.Vertex, discovered: dict):
    """
    图 g 中任意顶点 s 的广度优先搜索
    :param g: 图 Graph 类
    :param s: 顶点 Graph.Vertex 类
    :param discovered: 字典, 存储探索结果 {s (Vertex 类): None}
    :return: 权重和
    """
    level = [s]  # 第一层, 只有初始顶点 s
    weight_sum = 0

    while len(level) > 0:
        next_level = []  # 下一层的顶点集
        for u in level:  # 遍历本层所有点
            for e in g.incident_edges(u):  # 对 u 遍历所有边 e
                v = e.opposite(u)  # 找到边 e 的另一个端点 v
                if v not in discovered:  # 若 v 未标记
                    discovered[v] = e  # 则标记边 e
                    weight_sum += e.element()
                    next_level.append(v)  # 且存储点 v

        level = next_level  # 更新当前层
    return weight_sum


def BFS_allow_loop(g: Graph, s: Graph.Vertex, discovered: list):
    """
    图 g 中任意顶点 s 的广度优先搜索, 允许成环
    :param g: 图 Graph 类
    :param s: 顶点 Graph.Vertex 类
    :param discovered: 列表, 存储探索结果 []
    :return: 权重和
    """
    level = [s]  # 第一层, 只有初始顶点 s
    weight_sum = 0

    while len(level) > 0:
        next_level = []  # 下一层的顶点集
        for u in level:  # 遍历本层所有点
            for e in g.incident_edges(u):  # 对 u 遍历所有边 e
                v = e.opposite(u)  # 找到边 e 的另一个端点 v
                discovered.append((v, e))  # 则标记边 e
                weight_sum += e.element()
                next_level.append(v)  # 且存储点 v

        level = next_level  # 更新当前层

    return weight_sum
    # discovered = [(Vertex, Edge), (B, e(from s to B)), ...]


# ==================== Dijkstra 算法最短路 ====================
def shortest_path_lengths(g: Graph, src: Graph.Vertex, threshold=None) -> dict:
    """
    最短路径问题: Dijkstra 算法
    :param g: 图 Graph 类
    :param src: 源点 Graph.Vertex 类
    :param threshold: 阈值
    :return: 源点 src 到所有可达点 v 的最短距离 dict: {v: d[v]}
    """
    d = {}  # 记录所有点的标签 d[v]
    cloud = {}  # 存储最终结果 {v: d[v]} 在云内的标签 (即最终最短路)
    pq = AdaptableHeapPriorityQueue()  # 优先级队列, 能够 O(1) 找到特定点, 值 (点 v)为 locator 字典的键
    pqlocator = {}  # 存储点 v 在优先级队列中的位置 {v: loc of v in pq (AdaptableHeapPriorityQueue.Locator 类)}

    # 初始化所有点 v 的标签 d[v]
    for v in g.vertices():
        if v is src:
            d[v] = 0  # 源点为 0
        else:
            d[v] = float('inf')  # 暂时记为正无穷大
        pqlocator[v] = pq.add(d[v], v)  # (最短路 d[v], 点 v) 放入优先级队列, 同时记录位置在 pqlocator

    while not pq.is_empty():
        key, u = pq.remove_min()  # 取出云外最小路 min d[v] out of cloud
        cloud[u] = key  # 放入云内 cloud[u] = key 因为存的时候 key = d[u]
        del pqlocator[u]  # pqlocator 删去点 u 在优先级队列里的位置

        for e in g.incident_edges(u):  # 所有通向点 u 的边 e
            v = e.opposite(u)  # 对面的点 v
            if v not in cloud:  # 若 v 不在云里
                wgt = e.element()  # 边权重
                new_dist = d[u] + wgt
                # 阈值判断
                if threshold is not None and new_dist >= threshold:
                    continue  # 超过阈值
                # 否则, 正常 Dijkstra
                if new_dist < d[v]:
                    d[v] = new_dist
                    pq.update(pqlocator[v], d[v], v)
    return cloud


# ==================== Floyd Warshall 算法最短路 ====================
def floyd_warshall_shortest_path(g: Graph) -> dict:
    """
    使用 Floyd-Warshall 算法计算图中所有顶点对的最短路径距离
    :param g: 图 Graph 类
    :return: 返回一个字典 {u: {v: distance}}
    其中 distance 是 u 到 v 的最短距离
    如果 u 和 v 之间不可达 distance = float('inf')
    """
    verts = list(g.vertices())  # 获取所有顶点
    n = len(verts)

    # 初始化距离字典, 格式为 dist[u][v] = distance
    dist = {u: {v: float('inf') for v in verts} for u in verts}

    # 设置对角线为 0
    for u in verts:
        dist[u][u] = 0

    # 初始化直接相连的边
    for u in verts:
        for v in verts:
            edge = g.get_edge(u, v)
            if edge is not None:
                dist[u][v] = edge.element()

    # Floyd-Warshall 算法
    for k in verts:  # 中间点 k
        for u in verts:  # 起点 u
            for v in verts:  # 终点 v
                # 如果经过 k 的路径更短，则更新
                if dist[u][k] + dist[k][v] < dist[u][v]:
                    dist[u][v] = dist[u][k] + dist[k][v]

    return dist


# ==================== 拓扑排序, 判断有向环 ====================
def topological_sort(g: Graph):
    """返回拓扑排序, 即不存在排序在后的点指向排序在前的点
    若存在有向环, 则返回的序列不包含图中所有点
    """
    topo = []  # 按拓扑顺序存储 Vertex 类
    ready = []  # 存储满足条件的点, 即不再影响图的成环性 (栈 stack)
    incount = {}  # 存储每个点的入度, 实时更新

    # 1. 获取所有点, 记录 {Vertex: in-degree}
    for u in g.vertices():
        incount[u] = g.degree(u, False)
        if incount[u] == 0:  # 入度为 0 可以作为起始点, 不受其他影响
            ready.append(u)

    # 2. 对每个点处理, 清空 ready
    while len(ready) > 0:
        u = ready.pop()
        topo.append(u)
        # 获取 u 的邻接点
        for e in g.incident_edges(u):
            v = e.opposite(u)
            incount[v] -= 1  # 前一点已加入 topo 结果, 则 v 度减 1
            if incount[v] == 0:
                ready.append(v)  # 直到此时 v 也成为了"起点"
    return topo


def exist_loop(g: Graph):
    """存在有向环, 存在则返回 True"""
    topo = topological_sort(g)  # [Vertex 类, ]
    all_nodes = g.vertices()  # Vertex 类的迭代器
    return len(topo) != len(all_nodes)


if __name__ == '__main__':
    g = Graph(directed=False)
    v1 = g.insert_vertex(1)
    v2 = g.insert_vertex(2)
    v3 = g.insert_vertex(3)
    v4 = g.insert_vertex(4)

    g.insert_edge(v1, v2, "a")
    g.insert_edge(v2, v3, "b")
    g.insert_edge(v3, v4, "c")
    g.insert_edge(v4, v1, "d")
    g.insert_edge(v1, v3, "e")
    g.insert_edge(v2, v4, "f")

    print(f"Graph is directed or not: {g.is_directed()}")

    print("=" * 15, "All Vertices", "=" * 15)
    for v in g.vertices():
        print(f"Vertex: {v.element()}")

    print("=" * 15, "All Edges", "=" * 15)
    for e in g.edges():
        print(f"Edge: {e.element()}")

    g.save_to_json("test.json")

    # reload
    g = Graph(directed=False)
    locators = g.load_from_json("test.json")

    print(f"Graph is directed or not: {g.is_directed()}")

    print("=" * 15, "All Vertices", "=" * 15)
    for v in g.vertices():
        print(f"Vertex: {v.element()}")

    print("=" * 15, "All Edges", "=" * 15)
    for e in g.edges():
        print(f"Edge: {e.element()}")

    for k in locators:
        print(f"uid {k}, v {locators[k].element()}")
