import os
import math
from django.conf import settings

try:
    from .data_structures import ProbeHashMap, AdaptableHeapPriorityQueue, Graph, BFS, BFS_allow_loop, \
        floyd_warshall_shortest_path
except ImportError:
    from data_structures import ProbeHashMap, AdaptableHeapPriorityQueue, Graph, BFS, BFS_allow_loop, \
        floyd_warshall_shortest_path


class ClientService:
    """用户信息网络"""

    def __init__(self):
        """初始化, 读取图数据, 若无则创建空图"""
        self.g = Graph(directed=True)  # 有向图, 存储用户关系
        self.client_data_file = os.path.join(settings.DATA_DIR, '03clients.json')
        self.client_uid_name_file = os.path.join(settings.DATA_DIR, '02client_uid_name.csv')

        # 加载数据, 返回定位器, {uid: Vertex 类}
        load_data = self.g.load_from_json(self.client_data_file)
        self.uid_to_name = self._load_uid_name(self.client_uid_name_file)  # {uid: name, ...}

        if not load_data:  # 如果文件为空, 则创建空的定位器
            self.locators = ProbeHashMap()
            self._max_uid = 0  # 主键, 自增
        else:
            self.locators = load_data[0]
            self._max_uid = load_data[1]

    # -------------------------- nonpublic method --------------------------
    def _load_uid_name(self, filename):
        """加载 id name 对照表"""
        uid_to_name = ProbeHashMap()
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.readlines()
            if len(content) != 0 and content[0] != '\n':
                for line in content:
                    if not line == '\n':
                        line = line.split(',')
                        uid, client_name = int(line[0]), line[1][:-1]
                        uid_to_name[uid] = client_name
        return uid_to_name

    def _save_uid_name(self, filename):
        """保存 id name 对照表"""
        writer = ""
        for k in self.uid_to_name:
            writer += str(k) + ',' + str(self.uid_to_name[k]) + '\n'
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(writer)

    # -------------------------- I/O method: save data --------------------------
    def save(self):
        """更新所有"""
        self.g.save_to_json(self.client_data_file)
        self._save_uid_name(self.client_uid_name_file)

    def only_save_graph(self):
        """只更新本地图文件 json, 因为考虑到对边操作不影响 id name 对照"""
        self.g.save_to_json(self.client_data_file)

    def only_save_uid_name(self):
        """只更新 id name 对照表"""
        self._save_uid_name(self.client_uid_name_file)

    # -------------------------- 增删改查 --------------------------
    def get(self, uid):
        """根据 uid 返回点 Vertex 类"""
        if uid not in self.locators:
            return None
        else:
            return self.locators[uid]

    def get_name(self, uid):
        """根据 uid 返回用户名"""
        if uid not in self.locators:
            return None
        else:
            return self.uid_to_name[uid]

    def get_relation(self, uid, vid):
        u, v = self.locators[uid], self.locators[vid]
        if u and v:
            return self.g.get_edge(u, v).element()
        return None

    def add(self, client_name: str):
        """增加一个新用户"""
        uid = self._max_uid + 1  # 获取最新 uid
        loc = self.g.insert_vertex(uid)  # 存储用户 uid 到图
        self.locators[uid] = loc  # 定位器
        self.uid_to_name[uid] = client_name  # 根据 uid 找到 name
        self._max_uid += 1  # 主键, 自增
        return uid

    def add_relation(self, uid, vid, weight):
        """
        根据 uid vid 给 u v 加边, 权重为 weight
        :param uid: 用户 uid
        :param vid: 用户 vid
        :param weight: 权重
        :return: 成功添加则为 True, 若原本已有/点有误, 则不操作并返回 False
        """
        # 1. 点是否合法
        u, v = self.get(uid), self.get(vid)
        if u and v:
            # 2. 边是否合法
            if not self.g.get_edge(u, v):
                self.g.insert_edge(u, v, -weight)  # 权重正负
                return True
        return False

    def remove(self, uid):
        """删除用户 u, 失败返回 False, 成功返回点的值 uid"""
        u = self.get(uid)  # Vertex or None
        if u:
            u_elem = self.g.remove_vertex(u)
            del self.locators[uid]  # 删除定位器中的元素
            del self.uid_to_name[uid]  # 删除 id 对照表中的元素
            return u_elem
        return False

    def remove_relation(self, uid, vid):
        """删除边 u-v, 成功则返回边权重, 否则返回 False"""
        u, v = self.get(uid), self.get(vid)
        if u and v:
            if self.g.get_edge(u, v):  # Edge 类 or None
                e_elem = self.g.remove_edge(u, v)
                return e_elem  # weight
        return False

    def update_name(self, uid, client_name):
        """修改用户名, 成功则返回原名, 否则为 False"""
        u = self.get(uid)
        if u:
            old = self.g.update_vertex(u, client_name)
            old = self.uid_to_name[old]
            self.uid_to_name[uid] = client_name  # 修改 id 对照表
            return old
        return False

    def update_relation(self, uid, vid, weight):
        """修改关系重要程度, 成功则返回旧 weight, 否则返回 False"""
        u, v = self.get(uid), self.get(vid)
        if u and v:
            old = self.g.update_edge(u, v, -weight)
            return old
        return False

    def influence(self, uid, loop):
        """
        计算影响, 采用简单的权重加和
        :param uid: 点的独有记号
        :param loop: 是否运行成环
        :return: (影响和(sum of weight), 连通路径 path 点集, 连通路径 path 边集)
        """
        u = self.get(uid)
        weight_sum, discovered_v, discovered_e = None, None, None
        if u:
            discovered_v = set()
            discovered_v.add(u)
            if loop:
                discovered = []
                weight_sum = BFS_allow_loop(self.g, u, discovered)
                discovered_e = set()
                for v, e in discovered:
                    discovered_v.add(v)
                    discovered_e.add(e)
            else:
                discovered = {u: None}
                weight_sum = BFS(self.g, u, discovered)
                discovered_v = set(discovered.keys())
                discovered_e = set(discovered.values())
        return -weight_sum, discovered_v, discovered_e

    def all_influence(self):
        """Floyd 算法得到最短路
        [(Vertex, influence), ...] from influence small to large
        """
        res = {}
        dis = floyd_warshall_shortest_path(self.g)

        for u in dis:
            dis_list_of_u = []
            for v in dis[u]:
                if dis[u][v] < float('inf'):
                    dis_list_of_u.append(dis[u][v])

            if len(dis_list_of_u) > 1:
                dis_u_bar = sum(dis_list_of_u) / len(dis_list_of_u)
                dis_u_sd = sum([(x - dis_u_bar) ** 2 for x in dis_list_of_u]) / (len(dis_list_of_u) - 1)
                ci_left = dis_u_bar - 2 * dis_u_sd

                dis_u_sum = 0
                num = 0
                for i in range(len(dis_list_of_u)):
                    if dis_list_of_u[i] > ci_left:
                        dis_u_sum += dis_list_of_u[i]
                        num += 1
                if num > 0:
                    res[u] = dis_u_sum
                else:
                    res[u] = None
            elif len(dis_list_of_u) == 1:
                res[u] = dis_list_of_u[0]
            else:
                res[u] = None

        # 这里就简单实现一下排序, 不是终点
        return sorted(res.items(), key=lambda x: x[1], reverse=False)


if __name__ == '__main__':
    client_service = ClientService()

    client_service.add("Client1")
    client_service.add("Client2")
    client_service.add("Client3")
    client_service.add("Client4")
    client_service.add("Client5")
    client_service.add("Client6")

    client_service.add_relation(1, 2, 12)
    client_service.add_relation(1, 3, 13)
    client_service.add_relation(1, 4, 14)
    client_service.add_relation(1, 5, 15)
    client_service.add_relation(1, 6, 16)

    client_service.add_relation(2, 3, 23)
    client_service.add_relation(2, 4, 24)

    client_service.add_relation(3, 4, 34)
    client_service.add_relation(3, 6, 36)

    client_service.add_relation(5, 6, 56)

    print(client_service.uid_to_name)

    # client_service.remove_relation(1, 2)

    # client_service.remove(1)

    # print(client_service.uid_to_name)

    client_service.save()
