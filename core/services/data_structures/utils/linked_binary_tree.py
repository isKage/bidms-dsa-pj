class Tree:
    """树的抽象基础类，基础方法需要子类定义"""

    # ---------------- 抽象方法: 节点类 具体实现由子类实现 ----------------
    class Position:
        """每个元素的位置/节点类"""

        def element(self):
            # 由子类定义
            raise NotImplementedError('must be implemented by subclass')

        def __eq__(self, other):
            """比较节点是否相同"""
            # 由子类定义
            raise NotImplementedError('must be implemented by subclass')

        def __ne__(self, other):
            """比较节点是否不同"""
            return not (self == other)

    # ---------------- 抽象方法: 树的抽象基础类 具体实现由子类实现 ----------------
    def root(self):
        """返回根节点"""
        raise NotImplementedError('must be implemented by subclass')

    def parent(self):
        """返回父节点"""
        raise NotImplementedError('must be implemented by subclass')

    def num_children(self, p):
        """返回节点 p 下的子节点数目"""
        raise NotImplementedError('must be implemented by subclass')

    def children(self, p):
        """迭代器方式返回 p 节点的子类"""
        raise NotImplementedError('must be implemented by subclass')

    def __len__(self):
        """树的所有节点数目"""
        raise NotImplementedError('must be implemented by subclass')

    # ---------------- 具体方法: 如果抽象方法被子类定义后 ----------------
    def is_root(self, p):
        """判断 p 节点是否为根节点"""
        return self.root() == p

    def is_leaf(self, p):
        """判断 p 节点是否为叶子节点"""
        return self.num_children(p) == 0

    def is_empty(self):
        """判断树是否为空"""
        return len(self) == 0

    # 计算深度算法
    def depth(self, p):
        """返回节点 p 的深度，即到根节点的路径距离"""
        if self.is_root(p):
            # 根节点深度为 0
            return 0
        else:
            # 递归：当前节点的深度 = 父节点的深度 + 1
            return 1 + self.depth(self.parent(p))

    # 计算高度算法
    def height(self, p):
        """返回节点 p 的高度，即距离其最远叶子节点的路径长"""
        if self.is_root(p):
            # 叶子节点高度为 0
            return 0
        else:
            # 当前节点的高度 = 所有子节点高度最大值 + 1
            return 1 + max(self.height(c) for c in self.children(p))

    # ---------------- 深度优先：前/后序遍历 ----------------
    def __iter__(self):
        """定义迭代器：遍历方式可选"""
        for p in self.positions():  # positions() 可选不同的遍历方式
            yield p.element()

    def positions(self):
        """由子类具体指定 positions 方法"""
        raise NotImplementedError('must be implemented by subclass')

    def preorder(self):
        """前序遍历"""
        raise NotImplementedError('must be implemented by subclass')

    def _subtree_preorder(self, p):
        """前序遍历子树"""
        raise NotImplementedError('must be implemented by subclass')

    def postorder(self):
        """后序遍历"""
        raise NotImplementedError('must be implemented by subclass')

    def _subtree_postorder(self, p):
        """后序遍历子树"""
        raise NotImplementedError('must be implemented by subclass')


class BinaryTree(Tree):
    """二叉树的抽象基类，继承 Tree，一些方法暂不定义"""

    # ---------------- 新增的抽象方法: 具体实现由子类实现 ----------------
    def left(self, p):
        """返回当前节点 p 的左孩子节点"""
        raise NotImplementedError('must be implemented by subclass')

    def right(self, p):
        """返回当前节点 p 的右孩子节点"""
        raise NotImplementedError('must be implemented by subclass')

    # ---------------- 具体方法: 如果抽象方法被子类定义后 ----------------
    def sibling(self, p):
        """返回当前节点 p 的兄弟节点"""
        parent = self.parent(p)  # 获取父节点
        if parent is None:
            # 根节点无兄弟节点
            return None
        else:
            # 非左即右
            if p == self.left(parent):
                return self.right(parent)
            else:
                return self.left(parent)

    def children(self, p):
        """以迭代器的方式返回子节点（先左后右）"""
        if self.left(p) is not None:
            yield self.left(p)
        if self.right(p) is not None:
            yield self.right(p)

    # ---------------- 深度优先：二叉树的中序遍历 ----------------
    def __iter__(self):
        """定义迭代器：遍历方式可选"""
        for p in self.positions():  # positions() 可选不同的遍历方式
            yield p.element()

    def positions(self):
        """由子类具体指定 positions 方法"""
        raise NotImplementedError('must be implemented by subclass')

    def inorder(self):
        """中序遍历"""
        raise NotImplementedError('must be implemented by subclass')

    def _subtree_inorder(self, p):
        """中序遍历子树"""
        raise NotImplementedError('must be implemented by subclass')


class LinkedBinaryTree(BinaryTree):
    """链式结构的二叉树"""

    # ---------------- 非公开节点类 ----------------
    class _Node:
        """非公开节点类"""
        __slots__ = '_element', '_parent', '_left', '_right'

        def __init__(self, element, parent=None, left=None, right=None):
            self._element = element
            self._parent = parent
            self._left = left
            self._right = right

    # ---------------- 公有的节点类 ----------------
    class Position(BinaryTree.Position):
        """覆写父类 BinaryTree 的显式节点类"""

        def __init__(self, container, node):
            """具体初始化"""
            self._container = container  # 标记属于的树
            self._node = node

        def element(self):
            """具体实现返回元素值"""
            return self._node._element

        def __eq__(self, other):
            """具体实现 =="""
            return type(other) is type(self) and other._node is self._node

    # ---------------- 封装公有节点类 Position ----------------
    def _validate(self, p):
        """在封装 Position 类前判断节点 p 是否合法"""
        if not isinstance(p, self.Position):
            # 不是合法的节点类
            raise TypeError('p must be proper Position type')
        if p._container is not self:
            # 不属于当前树
            raise ValueError('p does not belong to this container')
        if p._node._parent is p._node:
            raise ValueError('p is no longer valid')
        return p._node

    def _make_position(self, node):
        """根据接受的节点类 _Node 封装为一个 Position 类"""
        if node is not None:
            return self.Position(self, node)
        else:
            return None

    # ---------------- 二叉树具体实现 ----------------
    def __init__(self):
        """初始化一个空的二叉树"""
        self._root = None
        self._size = 0

    # ---------------- 二叉树公有方法具体实现：覆写父类方法 ----------------
    def __len__(self):
        """返回树的节点总数"""
        return self._size

    def root(self):
        """返回根节点"""
        return self._make_position(self._root)  # 返回 self.Position 类

    def parent(self, p):
        """返回父节点"""
        node = self._validate(p)  # 判断合法并返回合法对象
        return self._make_position(node._parent)  # 封装为 Position 返回

    def left(self, p):
        """返回左子节点"""
        node = self._validate(p)
        return self._make_position(node._left)

    def right(self, p):
        """返回右子节点"""
        node = self._validate(p)
        return self._make_position(node._right)

    def num_children(self, p):
        """返回孩子节点数目"""
        node = self._validate(p)
        count = 0
        if node._left is not None:
            count += 1
        if node._right is not None:
            count += 1
        return count

    # ---------------- 二叉树非公有方法具体实现：一些对树的操作 ----------------
    def _add_root(self, e):
        """填入根元素，并返回封装后的 Position 类"""
        if self._root is not None:
            raise ValueError('Root exists')

        self._size = 1
        self._root = self._Node(e)  # 创建节点
        return self._make_position(self._root)  # 封装返回

    def _add_left(self, p, e):
        """在节点 p 下加左子节点，并返回封装后的类"""
        node = self._validate(p)  # 判断是否合法

        if node._left is not None:
            raise ValueError('Left node exists')

        self._size += 1
        node._left = self._Node(e, parent=node)  # 父节点为 node
        return self._make_position(node._left)

    def _add_right(self, p, e):
        """在节点 p 下加右子节点，并返回封装后的类"""
        node = self._validate(p)
        if node._right is not None:
            raise ValueError('Right node exists')
        self._size += 1
        node._right = self._Node(e, parent=node)
        return self._make_position(node._right)

    def _replace(self, p, e):
        """替换节点 p 的元素值，并返回旧元素"""
        node = self._validate(p)
        old = node._element
        node._element = e
        return old

    def _delete(self, p):
        """删除节点 p 用其孩子替代。当 p 非法或有两个孩子则报错"""
        node = self._validate(p)  # p 非法与否

        if self.num_children(p) == 2:  # p 有 2 个孩子
            raise ValueError('p has two children')

        # 取 p 的孩子节点
        child = node._left if node._left is not None else node._right

        if child is not None:
            # 子节点连接父节点的父节点
            child._parent = node._parent
        if node is self._root:
            # 父节点为根节点则子节点成为新根节点
            self._root = child
        else:
            # 更新父节点的父节点的孩子节点
            parent = node._parent
            if node is parent._left:
                parent._left = child
            else:
                parent._right = child
        self._size -= 1  # 节点数减一
        node._parent = node  # 惯例：self.parent -> self
        return node._element

    def _attach(self, p, t1, t2):
        """将子树 t1, t2 作为 p 的左右子节点连入树"""
        node = self._validate(p)
        if not self.is_leaf(p):
            raise ValueError('position must be leaf')
        if not type(self) is type(t1) is type(t2):  # 三个树类型必须相同
            raise TypeError('Tree types must match')

        self._size += len(t1) + len(t2)  # 更新节点数
        if not t1.is_empty():
            t1._root._parent = node
            node._left = t1._root
            t1._root = None
            t1._size = 0
        if not t2.is_empty():
            t2._root._parent = node
            node._right = t2._root
            t2._root = None
            t2._size = 0


if __name__ == '__main__':
    lbt = LinkedBinaryTree()
    print(len(lbt))
    print(lbt.root())
