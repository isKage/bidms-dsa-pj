import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BiDms.settings")
django.setup()  # os.environ['DJANGO_SETTINGS_MODULE']

import os
import shelve

import time
import random
import string

from django.conf import settings

try:
    from .data_structures import BPlusTree
except ImportError:
    from data_structures import BPlusTree

PRODUCTS_DATA_DIR = os.path.join(settings.DATA_DIR, '05products_plus')
UID_MAP = os.path.join(settings.DATA_DIR, '06products_plus_uid_price')


class Product:
    """商品类 Product"""

    def __init__(self, uid, name, price):
        self.uid = uid  # 商品 uid 主键
        self.name = name  # 商品名
        self.price = price  # 价格

    def __repr__(self):
        """重新命名属性名"""
        return f"Product(uid={self.uid}, name={self.name}, price={self.price})"


class BlockManager:
    """
    数据在磁盘中的存储形式
    {price: [Product(uid, name, price), Product(uid, name, price), ...]} 例如:
    {
        "699": [Product(uid=1, name="Item1", price=699), Product(uid=2, name="Item2", price=699)],
        "799": [Product(uid=3, name="Item3", price=799)],
    }
    """

    def __init__(self, filename=PRODUCTS_DATA_DIR):
        """数据以二进制的方式存储在 filename.db 中"""
        self.db = shelve.open(filename, writeback=True)

    # -------------------- 二进制文件: 读/写/删/查 --------------------
    def read_block(self, price):
        """根据 price 获取商品 Product 类的列表
         形如: [Product(uid, name, price), Product(uid, name, price), ...]"""
        return self.db.get(str(price), [])

    def write_block(self, price, products):
        """写入以二进制的方式磁盘"""
        self.db[str(price)] = products
        self.db.sync()  # 将内存中的所有更改同步到磁盘, 可加可不加, 最后 close 时仍然会保存

    def delete_block(self, price):
        """删除 price 整个数据块"""
        if str(price) in self.db:
            del self.db[str(price)]
            self.db.sync()

    # -------------------- 关闭二进制文件 --------------------
    def close(self):
        self.db.close()


class UIDMap:
    """存储 uid 的存储关系
    形如: {uid: price, uid: price, ...}"""

    def __init__(self, filename=UID_MAP):
        self.db = shelve.open(filename, writeback=True)
        self._max_uid = 0
        self._size = self._load_max_uid()

    def __len__(self):
        return self._size

    # -------------------- uid 生成方式封装 --------------------
    def _load_max_uid(self):
        """加载数据库中的最大 UID"""
        length = 0
        if self.db:
            # 获取所有的 uid
            all_uids = [int(k) for k in self.db.keys()]
            length = len(all_uids)
            if all_uids:
                self._max_uid = max(all_uids)
            else:
                self._max_uid = 0  # 如果没有任何记录, 初始化为 0

        return length

    def get_max_uid(self):
        """返回当前的最大 uid"""
        return self._max_uid

    def increment_uid(self):
        """获取下一个 uid"""
        self._max_uid += 1
        return self._max_uid

    # -------------------- 更新 uid 索引 --------------------
    def set(self, uid, price):
        """形如 {uid: price, uid: price, ...}"""
        self.db[str(uid)] = price
        self.db.sync()

    def get(self, uid):
        return self.db.get(str(uid), None)

    def delete(self, uid):
        if str(uid) in self.db:
            del self.db[str(uid)]
            self.db.sync()

    # -------------------- 其他 --------------------
    def all_items(self):
        """返回数据库中所有的 uid 和 price 对 [uid: price, uid: price, ...]"""
        return [(int(k), v) for k, v in self.db.items()]

    # -------------------- 关闭二进制文件 --------------------
    def close(self):
        self.db.close()


class ProductService:
    """商品服务"""

    def __init__(self):
        self.tree = BPlusTree()  # B+ 树
        self.block_manager = BlockManager()  # 真实数据硬盘存储管理 {price: Product}
        self.uid_index = UIDMap()  # uid price 索引硬盘存储管理 {uid: price}
        self._size = len(self.uid_index)
        self._iter = self._reader()

        # 加载本地数据
        self._rebuild_index()

    def __len__(self):
        """返回数据量"""
        return self._size

    # -------------------- nonpublic method --------------------
    def _rebuild_index(self):
        """"读取磁盘上的所有价格块 {uid: price}, 插入 B+ 树"""
        discovered = set()  # 记录所有 price (price 作为树的 key)
        for uid, price in self.uid_index.all_items():
            if price not in discovered:
                self.tree.insert(price, True)
                discovered.add(price)

    def _reader(self):
        for price, products in self.block_manager.db.items():
            for product in products:
                yield product

    # -------------------- 增/删/改/查 --------------------
    def find_product_by_uid(self, uid):
        """根据 UID 查找商品, 返回 Product 类"""
        price = self.uid_index.get(uid)  # 获取 price (key)
        if price is None:  # 未找到
            return None

        # 找到索引 key = price 则进入真实数据文件读取 {price：[Product, ...]}
        products = self.block_manager.read_block(price)
        for product in products:  # O(price 桶中 Product 数)
            if product.uid == uid:  # 找到符合 uid 的商品
                return product
        return None

    def add_product(self, name, price):
        """
        增加新商品, uid 自动添加
        :param name: 商品名
        :param price: 价格
        :return:
        """
        new_uid = self.uid_index.increment_uid()  # 获取新的 uid
        self.uid_index.set(new_uid, price)  # 保存此时的 uid: price

        product = Product(new_uid, name, price)  # 创建商品 Product 类

        if self.tree.search(price) is None:  # 寻找是否有价格重合的商品桶
            self.tree.insert(price, True)  # 无则插入 B+ 树 (创建新的 key = price), value = True 占位

        # 有则在二进制文件中直接添加 (即直接在 key = price 的桶中添加)
        products = self.block_manager.read_block(price)
        products.append(product)

        # 最新结果保存进本地文件
        self.block_manager.write_block(price, products)
        self._size += 1

    def remove_product(self, uid):
        """
        根据 uid 删除商品
        :param uid: 商品唯一编号
        :return: True or False
        """
        price = self.uid_index.get(uid)  # 获取对应的 price
        if price is None:  # 不存在则返回 False
            return False

        # 否则寻找 price 对应的数据块 {price: [Product, ...], ...}
        products = self.block_manager.read_block(price)
        # 除去 uid 商品的其他商品
        other_products = [p for p in products if p.uid != uid]

        if not other_products:  # 若删除 uid 后桶为空
            self.block_manager.delete_block(price)  # 则删去整个 price 数据
            self.tree.delete(price)  # 从树结构也删去 price
        else:
            # 否则, 直接保存其他商品即可
            self.block_manager.write_block(price, other_products)

        # 索引对照表删去 {uid: price}
        self.uid_index.delete(uid)
        return True

    def update_product(self, uid, new_name=None, new_price=None):
        """
        更新 name 和 price
        :param uid: 商品 uid 不允许更改, 只用于查找
        :param new_name: 更新后的 name
        :param new_price: 更新后的 price
        :return:
        """
        old_price = self.uid_index.get(uid)  # price 是键, 先查找
        if old_price is None:
            return False  # B+ 树结构中不存在 key = price

        # 进入真实数据读取 price 的商品 {price: [Product, ...]}
        products = self.block_manager.read_block(old_price)
        for p in products:
            if p.uid == uid:  # 找到需要被修改的商品
                # 如果价格变化, 采用删除节点再重新插入节点的方法
                if new_price is not None and new_price != old_price:
                    self.remove_product(uid)
                    self.add_product(new_name, new_price)
                # 否则, 只更新名字 name
                else:
                    if new_name:
                        p.name = new_name
                        self.block_manager.write_block(old_price, products)
                return True
        return False

    def find_products_in_price_range(self, min_price, max_price):
        """
        查找一定 price 间的商品数据
        :param min_price: 搜索的最小 price
        :param max_price: 搜索的最大 price
        :return: 商品列表 [Product 类, ...]
        """
        # B+ 树的范围搜索
        price_isLeaf_list = self.tree.search_range(min_price, max_price)
        # [(key, value), ] ==> [(price, True/False 占位)]

        result = []
        for price, _ in price_isLeaf_list:
            # 读取真正数据, 商品桶 [Product, ...]
            products = self.block_manager.read_block(price)
            result.extend(products)  # 直接并入 result
        return result

    # -------------------- 其他 --------------------
    def find_n_products(self, n):
        """返回 n 个商品, 用于展示 (不推荐, 建议直接从二进制数据库文件中读取)"""
        results = []
        node = self.tree.root  # 从根节点开始搜索

        while not node.is_leaf:  # 数据只存储在叶子节点上
            node = node.children[0]

        while node and len(results) < n:  # n 个
            for price in node.keys:  # 找到对应的数据索引 price (key)
                products = self.block_manager.read_block(price)  # 读取数据
                for p in products:
                    results.append(p)  # 将真正的产品数据加入 result
                    if len(results) >= n:
                        break
                if len(results) >= n:
                    break
            node = node.next  # 若不足继续前往下个节点 (leaf node 链式相连)
        return results

    def read_next(self, batch_size=10):
        """不建议使用, 可以考虑将 uid price 对照表存储为 csv 文件, 按照跳行的方式读取任意 [m, n] 行区间的数据"""
        batch = []
        for _ in range(batch_size):
            try:
                batch.append(next(self._iter))
            except StopIteration:
                break  # 数据读完
        return batch

    def __iter__(self):
        """迭代器获取商品"""
        node = self.tree.root  # 从根节点开始搜索

        while not node.is_leaf:  # 数据只存储在叶子节点上
            node = node.children[0]

        while node:  # n 个
            for price in node.keys:  # 找到对应的数据索引 price (key)
                products = self.block_manager.read_block(price)  # 读取数据
                for p in products:
                    yield p
            node = node.next  # 继续前往下个节点

    def close(self):
        """关闭 I/O 读写"""
        self.block_manager.close()
        self.uid_index.close()


# -------------------- 生成测试数据 --------------------
def random_name(length=10):
    """生成随机商品名称"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_price(start=1, end=1000):
    """生成随机价格"""
    return random.randint(start, end)


if __name__ == '__main__':
    """
    All Data: 101132
    Add one time: 0.02136499881744385
    Search one time: 0.00011587142944335938
    """
    product_service = ProductService()
    # print(product_service.find_products_in_price_range(0, 2))

    N = 10
    start = time.time()
    for i in range(N):
        product_service.add_product(random_name(), random_price())
    add_one_time = (time.time() - start) / N

    # start = time.time()
    # product_service.add_product(random_name(), random_price())
    # add_one_time = time.time() - start

    max_uid = product_service.uid_index.get_max_uid()

    start = time.time()
    print("search one example: ", product_service.find_product_by_uid(int(max_uid)))
    search_one_time = time.time() - start

    data_number = len(product_service)
    print(f"\nAll Data: {data_number}\nAdd one time: {add_one_time}\nSearch one time: {search_one_time}")

    read_10 = product_service.read_next(batch_size=10)
    print(f"\nRead 10: {read_10}")

    read_10 = product_service.read_next(batch_size=10)
    print(f"\nRead 10: {read_10}")

    # print(product_service.find_n_products(10))
    # for p in product_service:
    #     print(p)
    #     break

    product_service.close()

    """
    ```bash
    hexdump -C 05products_plus.db | less
    ```
    """
