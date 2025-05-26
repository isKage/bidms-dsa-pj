import struct
import os

T = 3
ORDER = T
KEY_SIZE = 8  # 每个键占 8 字节
OFFSET_SIZE = 8  # 每个值占 8 字节
MAX_KEYS = (2 * T - 1)
CHILDREN_SIZE = MAX_KEYS + 1
NODE_SIZE = 1 + MAX_KEYS * KEY_SIZE + CHILDREN_SIZE * OFFSET_SIZE + 8

FILENAME = "test_data/btree.db"


def from_bytes(data, offset):
    """从字节解析节点"""
    is_leaf = bool(data[0])
    keys = [struct.unpack_from("q", data, 1 + i * KEY_SIZE)[0] for i in range(MAX_KEYS)]
    keys = [k for k in keys]

    children = [struct.unpack_from("q", data, 1 + MAX_KEYS * KEY_SIZE + i * OFFSET_SIZE)[0] for i in
                range(CHILDREN_SIZE)]
    children = [c if c != -1 else None for c in children]

    n = struct.unpack_from("q", data, NODE_SIZE - 8)[0]

    return DiskBTree.DiskBTreeNode(is_leaf, keys, children, offset, n)


def create_node(is_leaf=True, keys=None, children=None, offset=None):
    return DiskBTree.DiskBTreeNode(is_leaf, keys, children, offset)


class DiskBTree:
    """B 树"""

    class DiskBTreeNode:
        """B 树的节点"""

        def __init__(self, is_leaf=True, keys=None, children=None, offset=None, n=0):
            """初始化 B 树节点类"""
            self.is_leaf = is_leaf  # 是否为叶子节点
            self.keys = [0] * MAX_KEYS if keys is None else keys  # key e.g. uid
            self.children = [None] * CHILDREN_SIZE if children is None else children  # 下一节点的偏移量
            self.offset = offset  # 当前节点的文件偏移位置
            self.n = n  # Current number of keys

        def to_bytes(self):
            """序列化节点为字节"""
            data = bytearray(NODE_SIZE)
            data[0] = 1 if self.is_leaf else 0

            # 编码 keys
            for i, key in enumerate(self.keys):
                struct.pack_into("q", data, 1 + i * KEY_SIZE, key)  # 'q' 表示 8 字节整数

            # 编码 children
            for i, child in enumerate(self.children):
                child = child if child is not None else -1
                struct.pack_into("q", data, 1 + MAX_KEYS * KEY_SIZE + i * OFFSET_SIZE, child)  # 'q' 表示 8 字节整数

            struct.pack_into("q", data, NODE_SIZE - 8, self.n)

            return bytes(data)

        def __repr__(self):
            return f"BTreeNode(is_leaf={self.is_leaf}, keys={self.keys[:self.n]}, num_keys={self.n}, children={self.children}, offset={self.offset})"

        def split_child(self, i, y):
            """分裂子节点"""
            z = create_node(is_leaf=y.is_leaf)

            z.n = T - 1

            for j in range(T - 1):
                z.keys[j] = y.keys[j + T]

            if not y.is_leaf:
                for j in range(T):
                    z.children[j] = y.children[j + T]

            y.n = T - 1

            for j in range(self.n, i, -1):
                self.children[j + 1] = self.children[j]

            DiskBTree.write_node(z)
            self.children[i + 1] = z.offset

            for j in range(self.n - 1, i - 1, -1):
                self.keys[j + 1] = self.keys[j]

            self.keys[i] = y.keys[T - 1]
            self.n += 1

            DiskBTree.write_node(y)
            DiskBTree.write_node(self)

        def insert_non_full(self, k):
            """非满节点的插入"""
            i = self.n - 1

            if self.is_leaf:
                while i >= 0 and self.keys[i] > k:
                    self.keys[i + 1] = self.keys[i]
                    i -= 1

                self.keys[i + 1] = k
                self.n += 1
            else:
                while i >= 0 and self.keys[i] > k:
                    i -= 1

                i += 1
                node = DiskBTree.read_node(self.children[i])
                if node.n == (2 * T - 1):
                    self.split_child(i, node)

                    if self.keys[i] < k:
                        i += 1

                node = DiskBTree.read_node(self.children[i])
                node.insert_non_full(k)

                DiskBTree.write_node(node)
                DiskBTree.write_node(self)

    # ----------------------- B 树定义 -----------------------
    def __init__(self, root_offset=None):
        """初始化 B 树"""
        # 设置根节点
        if root_offset is None:
            self.root = None
        else:
            self.root = DiskBTree.read_node(root_offset)  # 从磁盘读入根节点

    def insert(self, k):
        if self.root is None:
            self.root = self.DiskBTreeNode()
            self.root.keys[0] = k
            self.root.n = 1
            DiskBTree.write_node(self.root)
        else:
            if self.root.n == (2 * T - 1):
                s = self.DiskBTreeNode(is_leaf=False)
                s.children[0] = self.root.offset
                DiskBTree.write_node(s)
                s.split_child(0, self.root)
                DiskBTree.write_node(s)

                i = 0
                if s.keys[0] < k:
                    i += 1

                node = self.read_node(s.children[i])
                node.insert_non_full(k)
                DiskBTree.write_node(node)
                self.root = s
                DiskBTree.write_node(self.root)
            else:
                self.root.insert_non_full(k)
                DiskBTree.write_node(self.root)

    def search(self, k):
        if self.root is None:
            return None

        def _search(node):
            i = 0
            # 在当前节点中寻找第一个大于等于 k 的 key
            while i < node.n and k > node.keys[i]:
                i += 1

            # 如果找到了等于的 key，直接返回
            if i < node.n and node.keys[i] == k:
                return node

            # 如果是叶子节点，且没找到，返回 None
            if node.is_leaf:
                return None

            # 递归在对应的子节点中继续查找
            next_offset = node.children[i]
            if next_offset is None:
                return None

            next_node = DiskBTree.read_node(next_offset)
            return _search(next_node)

        return _search(self.root)

    @classmethod
    def read_node(cls, offset):
        with open(FILENAME, 'rb') as f:
            f.seek(offset)
            data = f.read(NODE_SIZE)
            node = from_bytes(data, offset)
            # print(f"Node @ offset={offset} is {node}")
            return node

    @classmethod
    def write_node(cls, node, available=None):
        with open(FILENAME, 'r+b' if os.path.exists(FILENAME) else 'w+b') as f:
            # 先使用空余位置
            if available:
                node.offset = available

            # 若该节点还没有偏移量, 分配新偏移量（文件末尾）
            if node.offset is None:
                f.seek(0, os.SEEK_END)
                node.offset = f.tell()

            # 移动到指定偏移位置并写入节点数据
            f.seek(node.offset)
            f.write(node.to_bytes())

    def close(self):
        return self.root.offset


def traverse(filename):
    with open(FILENAME, 'rb') as f:
        offset = 0
        while True:
            f.seek(offset)
            data = f.read(NODE_SIZE)
            if len(data) == 0:
                break
            node = from_bytes(data, offset)
            print(node)
            offset += NODE_SIZE


if __name__ == '__main__':
    # k > 0
    print("One node size", NODE_SIZE)

    print("=" * 100, "\nInitial and Add Data\n", "-" * 100, sep="")
    tree = DiskBTree()
    keys_to_insert = [2, 3, 4, 5, 6, 12, 7, 8, 9, 10, 11, 15, 13]
    print(f"Add: {keys_to_insert}")
    for k in keys_to_insert:
        tree.insert(k)
    root_offset = tree.close()
    print(f"Root offset is {root_offset}")

    print("=" * 100, "\nLoad Data and Search\n", "-" * 100, sep="")
    tree = DiskBTree(root_offset)
    add_new = [1, 20, 30, 40, 50, 60, 70, 80, 90, 100, 21]
    print(f"Add new one: {add_new}")
    for k in add_new:
        tree.insert(k)

    print("The root: ", tree.root)
    print("Search 100: ", tree.search(100))
    print("Search 1: ", tree.search(1))
    print("Search 90: ", tree.search(90))
    print("Search 30: ", tree.search(30))
    root_offset = tree.close()
    print(f"Root offset is {root_offset}")

    """
    One node size 97
    ====================================================================================================
    Initial and Add Data
    ----------------------------------------------------------------------------------------------------
    Add: [2, 3, 4, 5, 6, 12, 7, 8, 9, 10, 11, 15, 13]
    Root offset is 97
    ====================================================================================================
    Load Data and Search
    ----------------------------------------------------------------------------------------------------
    Add new one: [1, 20, 30, 40, 50, 60, 70, 80, 90, 100, 21]
    The root:  BTreeNode(is_leaf=False, keys=[10], num_keys=1, children=[97, 776, None, None, None, None], offset=679)
    Search 100:  BTreeNode(is_leaf=True, keys=[70, 80, 90, 100], num_keys=4, children=[None, None, None, None, None, None], offset=873)
    Search 1:  BTreeNode(is_leaf=True, keys=[1, 2, 3], num_keys=3, children=[None, None, None, None, None, None], offset=0)
    Search 90:  BTreeNode(is_leaf=True, keys=[70, 80, 90, 100], num_keys=4, children=[None, None, None, None, None, None], offset=873)
    Search 30:  BTreeNode(is_leaf=False, keys=[13, 30, 60], num_keys=3, children=[388, 485, 582, 873, None, None], offset=776)
    Root offset is 679
    """
    # tree = DiskBTree(679)
    # print(tree.search(90))
    # print("=" * 100)
    #
    # traverse(FILENAME)
