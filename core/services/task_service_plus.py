import os
from django.conf import settings

try:
    from .data_structures import Graph, ProbeHashMap, topological_sort, exist_loop
    from .task_service import TaskService
except ImportError:
    from data_structures import Graph, ProbeHashMap, topological_sort, exist_loop
    from task_service import TaskService


class TaskServicePlus(TaskService):
    """升级版: 加入任务前后关系"""

    def __init__(self):
        super().__init__(os.path.join(settings.DATA_DIR, "08tasks_plus.csv"))
        self.g = Graph(directed=True)  # 存储优先关系图 A -> B 代表 B 先于 A
        self.task_relation_graph_file = os.path.join(settings.DATA_DIR, "07tasks_graph.json")

        # 定位器, 存储 {uid: Graph.Vertex 类}
        self._load_relation()  # 自主生成定位器 self.uid_vertex

    # -------------------------- nonpublic method --------------------------
    def _restruct_graph(self):
        """基于原本的 task 任务列表, 补充图结构"""
        for uid in self.locators:
            u = self.g.insert_vertex(uid)
            self.uid_vertex[uid] = u

    # -------------------------- 增删改查 --------------------------
    def add(self, task_name: str, urgency: int, impact: int):
        """覆写: 加入新任务"""
        uid = super().add(task_name, urgency, impact)  # 父类加入新任务

        # 在任务关系图中加入新点
        u = self.g.insert_vertex(uid)  # return Vertex
        self.uid_vertex[uid] = u
        return uid

    def remove(self, uid: int):
        """覆写: 删除任务 uid"""
        result = super().remove(uid)  # 父类方法, 删除 uid 任务在优先级队列和任务列表

        u = self.uid_vertex[uid]  # 获取任务在关系图中的 Vertex 类
        del self.uid_vertex[uid]  # 删除图定位器中 key = uid
        self.g.remove_vertex(u)  # 删除点
        return result

    def add_relation(self, uid, vid):
        """
        增加 uid -> vid 表示先完成 vid 才能完成 uid
        :param uid: 后置任务
        :param vid: 前置任务
        :return: 成环则返回 False 表示失败; 否则返回 True
        """
        if (uid not in self.uid_vertex) or (vid not in self.uid_vertex):
            raise KeyError(f"There is no Vertex {uid} or {vid}")
        u, v = self.uid_vertex[uid], self.uid_vertex[vid]

        # 尝试加入边 u -> v
        self.g.insert_edge(u, v)
        # 判断是否成环
        loop = exist_loop(self.g)
        if loop:
            self.g.remove_edge(u, v)
            return False
        return True

    def remove_relation(self, uid, vid):
        """删除任务关系"""
        if (uid not in self.uid_vertex) or (vid not in self.uid_vertex):
            return False
        u, v = self.uid_vertex[uid], self.uid_vertex[vid]
        self.g.remove_edge(u, v)
        return True

    # --------------------- I/O method ---------------------
    def save(self):
        super().save()
        self.g.save_to_json(self.task_relation_graph_file)

    def _load_relation(self):
        load_data = self.g.load_from_json(self.task_relation_graph_file)

        if not load_data:  # 如果文件为空, 则创建空的定位器
            self.uid_vertex = ProbeHashMap()
            self._restruct_graph()  # 补全图结构
        else:
            self.uid_vertex = load_data[0]


if __name__ == '__main__':
    task_service_plus = TaskServicePlus()

    print(len(task_service_plus.all_tasks()))
    print(len(task_service_plus.g.vertices()))

    # task_service_plus.add("New task 2", 200, 200)

    print(task_service_plus.add_relation(5, 9))
    print(task_service_plus.add_relation(9, 6))
    print(task_service_plus.add_relation(6, 5))

    print("=" * 100)
    print(len(task_service_plus.all_tasks()))
    print(len(task_service_plus.g.vertices()))

    print("=" * 100)
    print(task_service_plus.g.edges())

    task_service_plus.save()
