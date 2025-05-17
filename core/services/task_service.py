import os
from django.conf import settings

try:
    from .data_structures import ProbeHashMap, AdaptableHeapPriorityQueue
except ImportError:
    from data_structures import ProbeHashMap, AdaptableHeapPriorityQueue


class TaskList:
    """任务数据类 (不使用)"""

    class _LineData:
        """存储每一行的数据对象"""

        def __init__(self, uid, name, urgency, impact):
            self._uid = uid
            self._name = name
            self._urgency = urgency
            self._impact = impact

        @property
        def uid(self):
            return self._uid

        @property
        def name(self):
            return self._name

        @property
        def urgency(self):
            return self._urgency

        @property
        def impact(self):
            return self._impact

    def __init__(self, file_path):
        """一次性读取文件数据, 磁盘读写较慢, 内存操作更快, O(N) N 是行数"""
        self._data = []
        with open(file_path, "r") as f:
            content = f.readlines()
            for line in content:
                if not line == '\n':
                    line = line.split(',')
                    line = [int(line[0]), line[1], int(line[2]), int(line[3])]
                    self._data.append(self._LineData(line[0], line[1], line[2], line[3]))

    def all_tasks(self):
        """返回所有任务"""
        return self._data


class TaskService:
    """任务服务对象"""

    def __init__(self, file_path=os.path.join(settings.DATA_DIR, '01tasks.csv')):
        """初始化, 读取数据库中数据"""
        self.pq = AdaptableHeapPriorityQueue()  # 优先级队列, 实现了定位器
        self.locators = ProbeHashMap()  # 定位, {uid: Locator 类}
        self.task_data_file = file_path
        self._max_uid = 0  # 主键, 自增
        self._load_tasks(self.task_data_file)  # 加载数据

    def __len__(self):
        return len(self.pq)

    # -------------------------- nonpublic method --------------------------
    def _all_tasks(self, loc_list: list):
        """根据 locator 类列表返回所有信息
        [(uid, task_name, urgency, impact), ...]
        """
        data = []
        for loc in loc_list:
            newline = [val for val in loc._value]
            data.append(newline)
        return data

    def _load_tasks(self, file_path=None):
        """读取数据"""
        with open(file_path, "r") as f:
            content = f.readlines()
            if len(content) != 0 and content[0] != '\n':
                for line in content:
                    if not line == '\n':
                        line = line.split(',')
                        line = [int(line[0]), line[1], int(line[2]), int(line[3])]
                        if self._max_uid < line[0]:
                            self._max_uid = line[0]  # 找到目前最大主键

                        self._add(line[0], line[1], line[2], line[3])

    def _add(self, uid, task_name: str, urgency: int, impact: int):
        loc = self.pq.add(key=-urgency * impact, value=(uid, task_name, urgency, impact))
        self.locators[uid] = loc
        return uid

    # -------------------------- I/O method: save data --------------------------
    def save(self):
        """存入 csv 文件"""
        data = self._all_tasks(self.pq._data)
        writer = ""
        with open(self.task_data_file, "w") as f:
            for line in data:
                writer += str(line[0]) + "," + line[1] + "," + str(line[2]) + "," + str(line[3]) + "\n"
            f.writelines(writer)

    # -------------------------- 增删改查 --------------------------
    def add(self, task_name: str, urgency: int, impact: int):
        """插入新数据"""
        uid = self._max_uid + 1
        loc = self.pq.add(key=-urgency * impact, value=(uid, task_name, urgency, impact))
        self.locators[uid] = loc
        self._max_uid += 1  # 更新, 自增
        return uid  # 返回 uid 方便检索

    def remove(self, uid: int):
        """根据 uid 删除"""
        if uid in self.locators:
            loc = self.locators[uid]
            del self.locators[uid]  # 删除
            k, v = self.pq.remove(loc)
            return k, v  # k = -urgency * impact, v = uid, task_name, urgency, impact
        else:
            return False

    def remove_max(self):
        """存储的是负优先级, 所以堆中最小, 现实意义是最大"""
        k, v = self.max()
        uid = v[0]
        self.remove(uid)
        return k, v

    def update(self, uid: int, task_name: str, urgency: int, impact: int):
        """修改 uid 对应的元素"""
        loc = self.locators[uid]
        self.pq.update(
            loc=loc,
            newkey=-urgency * impact,
            newval=(uid, task_name, urgency, impact)
        )

    def max(self):
        """返回最大, 不删除"""
        k, v = self.pq.min()
        return k, v

    def get(self, uid: int):
        """查看 uid 对应的元素"""
        loc = self.locators[uid]
        return loc._key, loc._value

    # -------------------------- top k: deep copy --------------------------
    def nlargest_nlogk(self, k: int):
        """top k, k 个组成 k-heap, 然后比较剩下的 n - k 个, k-heap 和原始堆性质相反
        [(uid, task_name, urgency, impact), ...]
        """
        while k > len(self.pq):
            k = len(self.pq)  # k > n 则直接返回所有 k = n

        k_heap = AdaptableHeapPriorityQueue()
        # 将前 k 个复制到 k_heap 中 O(k log k)
        for loc in self.pq._data[:k]:
            k_heap.add(-loc._key, loc._value)  # - key 的最小堆

        # 与剩下的比较 O((n - k) log k)
        for loc in self.pq._data[k:]:
            if -loc._key > k_heap.min()[0]:
                k_heap.add(-loc._key, loc._value)
                k_heap.remove_min()

        # 返回 top k O(k log k)
        top_k = []
        while len(top_k) < k:
            _, v = k_heap.remove_min()
            top_k.append(v)

        # 倒序
        if k == 1:
            return top_k
        for i in range(k // 2):
            top_k[i], top_k[k - i - 1] = top_k[k - i - 1], top_k[i]

        return top_k

    def nlargest_klogn(self, k: int):
        """原始堆逐个返回 top k
        [(uid, task_name, urgency, impact), ...]
        """
        while k > len(self.pq):
            k = len(self.pq)

        heap_copy = AdaptableHeapPriorityQueue()
        # 完整复制一遍 O(n) 不需要冒泡
        for loc in self.pq._data:
            heap_copy.add(loc._key, loc._value)  # 正常添加 key 即可

        # 逐个 remove_min() k 个即可
        top_k = [None] * k
        for i in range(k):
            top_k[i] = heap_copy.remove_min()[1]  # loc._value
        return top_k

    # -------------------------- 其他 --------------------------
    def all_tasks(self):
        """返回当前堆里所有任务信息
        [(uid, task_name, urgency, impact), ...]
        """
        return self._all_tasks(self.pq._data)


if __name__ == '__main__':
    task_service = TaskService()
    N = 50
    for i in range(N):
        task_service.add('task' + str(i), i, i)

    # task_service.update(1, "task1_new", 11, 1)
    #
    # k, v = task_service.remove_max()
    # print(v)

    task_service.save()

    # task_service = TaskService()
    # print(task_service.nlargest_nlogk(4))
    # print(task_service.nlargest_klogn(4))
