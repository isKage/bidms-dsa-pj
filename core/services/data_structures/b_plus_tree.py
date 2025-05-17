try:
    from .utils import ArrayStack
except ImportError:
    from utils import ArrayStack  # 栈

# B+ 树阶数
ORDER = 3


class BPlusNode:
    """B+ 树的节点类"""

    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf  # 是否为叶子节点, 只有叶子节点存储真实数据的索引
        self.keys = []  # 存储本节点的键值
        self.children = []  # 存储子树的索引, 指向下一层的节点
        self.next = None  # 同一层是否有链式结构, 叶子节点键链式连接


class BPlusTree:
    """B+ 树类"""

    def __init__(self):
        self.root = BPlusNode(is_leaf=True)  # 初始根节点, 暂定为叶子节点
        self._size = 0  # 记录树的实际数据数量

    def __len__(self):
        """数据数量"""
        return self._size

    # -------------------- 增/删/改/查 --------------------
    def search(self, key):
        """
        根据键值查找节点
        :param key: 唯一键值
        :return: 节点 BPlusNode 类
        """
        node = self._search_leaf(key)  # node 是包含 key 的叶子节点

        # 再查找叶子 node 中 key 的具体位置
        for i, k in enumerate(node.keys):
            if k == key:
                return node.children[i]  # 此时返回的存储了真实数据的节点 BPlusNode 类
        return None

    def search_range(self, start, end):
        """
        查找范围数据 start <= key < end
        :param start: 起始 key
        :param end: 终止 key
        :return: BPlusNode 类列表 [BPlusNode, ...]
        """
        results = []  # 存储节点类

        # 1. 单点搜索: 找到包含键为 start 的叶子节点
        node = self._search_leaf(start)  # node 是包含 key = start 的叶子节点

        # 2. 因为叶子节点是链式存储, 可以从 start 开始遍历
        while node:
            for i, k in enumerate(node.keys):
                if k < start:
                    continue
                if k > end:
                    return results  # 直到超出了 end
                results.append((k, node.children[i]))  # 返回 (key, value) 对
            node = node.next
        return results  # 或者返回 [start, inf] 一直到最后

    def insert(self, key, value):
        """
        插入节点
        :param key: 唯一键值
        :param value: 存储的数据
        :return: None
        """
        if self.search(key) is not None:
            # 检查: 若 key 存在, 直接更新 value
            self.update_value(key, value)
            return

        root = self.root  # 从根搜索
        if len(root.keys) == ORDER:  # 根节点已满
            # 1. 创建新的根节点
            new_root = BPlusNode(is_leaf=False)
            new_root.children.append(self.root)

            # 2. 进行分裂
            self._split_child(new_root, 0)

            self.root = new_root  # 重新指定根节点

        # 非满节点中插入
        self._insert_non_full(self.root, key, value)

        self._size += 1  # 数据量增加

    def delete(self, key):
        """
        删除键为 key 的节点
        :param key: 按照键 key 查找
        :return: 被是否成功 True/False
        """
        deleted, shrink = self._delete(self.root, key)

        if deleted:  # 删除成功
            self._size -= 1  # 数量减 1

            # 根节点是否退化
            if not self.root.is_leaf and len(self.root.children) == 1:
                # 当根节点不是叶子节点 & 只有一个子节点时, 退化
                self.root = self.root.children[0]
        return deleted

    def update_value(self, key, new_value):
        """
        只更新键为 key 的节点的值
        :param key: 唯一键, 用于查找
        :param new_value: 新的值
        :return: 成功与否 True/False
        """
        # 找到包含该键的叶子节点
        node = self._search_leaf(key)

        # 直接更新值即可
        for i, k in enumerate(node.keys):
            if k == key:
                node.children[i] = new_value
                return True
        return False

    def update_key(self, old_key, new_key):
        """
        更新键值, 相当于先删除后插入
        :param old_key: 旧键值 key
        :param new_key: 新键值 key
        :return: 成功与否 True/False
        """
        value = self.search(old_key)  # 先查找 old_key
        if value is None:
            return False  # 若不存在, 则失败, 不可操作

        self.delete(old_key)  # 删除旧的
        self.insert(new_key, value)  # 加入新的, 不改变值 value
        return True

    # -------------------- nonpublic method --------------------
    def _search_leaf(self, key):
        """根据 key 查找键 key 所在的叶子节点"""
        node = self.root  # 从根节点查找

        while not node.is_leaf:  # 直到叶子节点 (存储数据, 键为 key)
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                # 直到找到 i 使得 node.keys[i] < key <= node.keys[i + 1]
                i += 1
            node = node.children[i]  # 去往对应的子树, 继续查找

        return node

    def _insert_non_full(self, node, key, value):
        """
        从 node 开始尝试插入键值对 (因为具体的值必须只能在叶子节点插入)
        :param node: 非满节点
        :param key: 需要被插入的键
        :param value: 需要被插入的值
        :return: None
        """
        # 1. 在叶子节点中插入
        if node.is_leaf:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:  # 找到插入位置
                i += 1
            # 因为是叶子节点, 所以直接插入即可
            node.keys.insert(i, key)
            node.children.insert(i, value)

        # 2. 在非叶子节点 (内部节点) 中插入
        else:  # 根据 key 找到被插入的 (key, value) 的正确叶子节点位置
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1  # 一个节点里寻找正确的位置
            child = node.children[i]  # 下一层

            if len(child.keys) == ORDER:  # 节点已满
                self._split_child(node, i)  # 分裂
                if key >= node.keys[i]:
                    i += 1

            # 当前位置, 递归调用插入函数
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent, index):
        """
        分裂子节点:
            叶子节点分裂: 复制后半部分键值到新节点, 保留前半部分在原节点
            内部节点分裂: 中间键提升到父节点, 剩余键平分到两个子节点
        :param parent: 父节点
        :param index: 需要被分裂的子节点在父节点 children 中的索引
        :return:
        """
        node = parent.children[index]  # 待分裂的节点
        mid = len(node.keys) // 2  # 计算分裂点的位置 (取中间)
        new_node = BPlusNode(is_leaf=node.is_leaf)  # 分裂出的一个新节点

        # 1. 叶子节点分裂
        if node.is_leaf:
            # 新节点获取后半部分键值
            new_node.keys = node.keys[mid:]
            new_node.children = node.children[mid:]

            # 原节点保留前半部分
            node.keys = node.keys[:mid]
            node.children = node.children[:mid]

            # 叶子节点满足链式结构
            new_node.next = node.next
            node.next = new_node

            # 新节点的第一个键 (min key) 提升到父节点
            parent.keys.insert(index, new_node.keys[0])  # 注: list.insert() 函数

            # 新节点添加到父节点的 children 中
            parent.children.insert(index + 1, new_node)

        # 2. 内部节点分裂
        else:
            # 中间键 (准备提升到父节点)
            up_key = node.keys[mid]

            # 将节点的键分配到分裂后的两个节点中
            left_keys = node.keys[:mid]  # 分配给左子节点的键
            right_keys = node.keys[mid + 1:]  # 分配给右子节点的键

            # 分裂出的子节点指针 (即指向下一层节点的指针)
            left_children = node.children[:mid + 1]  # 分配给左子节点
            right_children = node.children[mid + 1:]  # 分配给右子节点

            # 更新原节点, 即原节点变为分裂出的左节点
            node.keys, node.children = left_keys, left_children

            # 设置分裂出的右子节点
            new_node.keys, new_node.children = right_keys, right_children

            # 父节点链接新的分裂后的节点
            parent.keys.insert(index, up_key)  # 将中间键插入父节点, 即中间的键提升到了父节点
            parent.children.insert(index + 1, new_node)  # 新节点 (即右节点) 添加到父节点的 children 中

    def _delete(self, node, key):
        """
        对节点 node 尝试删除键 key, 考虑是否需要 fix (即合并节点/向兄弟节点借键)
        :param node: 传入的节点类, 尝试从 node 出发递归删除 key
        :param key: 准备被删除的键
        :return: (bool, bool) 代表 (是否删除成功, 是否需要修复)
        """
        # 1. node 是叶子节点
        if node.is_leaf:
            if key in node.keys:
                # 叶子节点删除, 只需要找到删除即可
                idx = node.keys.index(key)
                node.keys.pop(idx)
                node.children.pop(idx)

                # 检查是否需要修复: 删除的是叶子节点的边界值时, 需要修复父节点索引
                self._fix_parent_keys(node, key)

                # 删除成功, 修复: 节点的键数量是否 < (ORDER + 1) // 2
                min_key = (ORDER + 1) // 2 - 1
                return True, len(node.keys) < min_key

            return False, False  # 失败

        # 2. node 是内部节点
        else:
            # part 1 找到包含 k 的子节点
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1

            # part 2 从子节点开始递归删除
            deleted, need_fix = self._delete(node.children[i], key)

            if not deleted:
                return False, False  # 失败

            # part 3 是否需要修复 (合并节点 or 向兄弟节点借键)
            if need_fix:  # 需要修复
                # 获取左右兄弟节点
                left = node.children[i - 1] if i > 0 else None  # 超出则为 None, 表示没有
                right = node.children[i + 1] if i + 1 < len(node.children) else None
                min_key = (ORDER + 1) // 2 - 1

                curr = node.children[i]  # 当前需要修复的子节点, node 是父节点

                # situation 1 从左兄弟借一个键 (left > (阶数 + 1) // 2)
                if left and len(left.keys) > min_key:
                    if curr.is_leaf:
                        # 左兄弟的最后一个键, 移动到当前需要修复的节点 的 头部
                        curr.keys.insert(0, left.keys.pop(-1))
                        curr.children.insert(0, left.children.pop(-1))
                        node.keys[i - 1] = curr.keys[0]  # 更新父节点 keys list
                    else:
                        curr.keys.insert(0, node.keys[i - 1])
                        node.keys[i - 1] = left.keys.pop(-1)
                        curr.children.insert(0, left.children.pop(-1))
                    return True, False  # 成功

                # situation 2 从右兄弟借一个键 (right > (阶数 + 1) // 2)
                elif right and len(right.keys) > min_key:
                    if curr.is_leaf:
                        # 右兄弟的第一个键, 移动到当前修复的节点 的 尾部
                        curr.keys.append(right.keys.pop(0))
                        curr.children.append(right.children.pop(0))
                        node.keys[i] = right.keys[0]  # 更新父节点 keys list
                    else:
                        curr.keys.append(node.keys[i])
                        node.keys[i] = right.keys.pop(0)
                        curr.children.append(right.children.pop(0))
                    return True, False  # 成功

                # situation 3 合并节点 (left 和 right 的键均少)
                else:
                    if left:  # 有左兄弟节点, 则和左合并
                        if curr.is_leaf:
                            # 利用 list 直接合并 key 和 指针列表
                            left.keys += curr.keys
                            left.children += curr.children
                            left.next = curr.next
                        else:
                            left.keys.append(node.keys[i - 1])
                            left.keys += curr.keys
                            left.children += curr.children

                        # 删除父节点 node 中代表分隔的 key 和指针
                        node.keys.pop(i - 1)
                        node.children.pop(i)

                    elif right:  # 否则和左合并
                        if curr.is_leaf:
                            # 利用 list 直接合并 key 和 指针列表
                            curr.keys += right.keys
                            curr.children += right.children
                            curr.next = right.next
                        else:
                            curr.keys.append(node.keys[i])
                            curr.keys += right.keys
                            curr.children += right.children

                        # 删除父节点 node 中代表分隔的 key 和指针
                        node.keys.pop(i)
                        node.children.pop(i + 1)

                    # (删除成功, 继续检查父节点是否需要修复)
                    return True, len(node.keys) < ((ORDER + 1) // 2 - 1)

            # 不需要修复
            return True, False

    def _fix_parent_keys(self, node, key):
        """
        当叶子节点最小 key 删除时, 递归修复父节点中的索引
        :param node: 被删除 key 的叶子节点
        :param key: 键值
        :return: None
        """
        if node == self.root:  # 根节点无需修复
            return

        # 查找当前节点的父节点
        parent = self._find_parent(self.root, node)

        if not parent:  # 无父节点, 即根节点, 同样无需修复, 仅作为检查
            return

        # 遍历父节点的所有子节点检查
        for i, child in enumerate(parent.children):
            if child == node and i > 0:
                if parent.keys[i - 1] == key and node.keys:
                    # 检查父节点的分隔键 (即其子节点的边界上的键) 是否等于被删除的键
                    # 用当前节点新的最小键更新父节点
                    parent.keys[i - 1] = node.keys[0]
                # 递归向上修复
                self._fix_parent_keys(parent, key)
                break

    def _find_parent(self, current, child):
        """
        从 current 节点开始寻找 child 的父节点
        :param current: 查找起点 节点类
        :param child: 目标节点的子节点
        :return: BPlusNode or None
        """
        if current.is_leaf:
            return None  # 从叶子节点出发, 一定无法查找到父节点

        for c in current.children:
            if c == child:  # 遍历查找
                return current
            res = self._find_parent(c, child)  # 否则递归查找
            if res:  # 找到则返回
                return res
        return None  # 否则返回 None

    # -------------------- 其他: Debug 展示 --------------------
    def traverse(self):
        """"展示 B+ 数结构
        # Length: 13
        # Level 0: [[11]]
        # Level 1: [[4, 9], [11, 13]]
        # ...
        """
        # [打印]数据量
        print("# == B+ Tree == #")
        print(f"# Length: {len(tree)}")

        levels = []
        stack = ArrayStack()  # 栈
        stack.push((self.root, 0))

        while not stack.is_empty():
            node, lvl = stack.pop()
            if lvl >= len(levels):
                levels.append([])
            levels[lvl].append(node.keys)
            if not node.is_leaf:
                for child in node.children:
                    stack.push((child, lvl + 1))

        # [打印]每层数据
        for i, lv in enumerate(levels):
            print(f"# Level {i}: {lv}")

        self._print_leaves()  # 展示所有叶子节点的值

    def _print_leaves(self):
        """展示所有叶子节点的值, 即按顺序返回真实数据
        <__LeafChain([1, 2], [4], [4, 6], [7, 8], [9, 10], [11, 12], [13, 14, 15], None)__>
        """
        node = self.root
        while not node.is_leaf:
            node = node.children[0]  # 一直向左查找, 得到最小值

        # [打印]所有数据 (按照叶子节点存储结构)
        print("# LeafChain:", end="")
        while node:
            print(f"{node.keys}", end=" -> ")
            node = node.next
        print("None")


# 示例
if __name__ == '__main__':
    import string

    letters = string.ascii_lowercase[:12]
    elements = [(i, letters[i]) for i in range(len(letters))]
    print(elements)

    tree = BPlusTree()
    for k, v in elements:
        tree.insert(k, v)
    tree.traverse()

    print("=" * 100)
    print(f"key = 6, value = {tree.search(6)}")

    print("insert key = 100")
    tree.insert(100, "test")
    tree.traverse()

    print(f"delete key = 0")
    tree.delete(0)
    tree.traverse()

    print(tree.search_range(5, 11))
