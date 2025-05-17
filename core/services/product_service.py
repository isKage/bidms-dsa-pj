import os
import string
import random
from django.conf import settings

try:
    from .data_structures import AVLTreeMap, ProbeHashMap
    from .data_structures.utils import find_all_from_list
except ImportError:
    from data_structures import AVLTreeMap, ProbeHashMap
    from data_structures.utils import find_all_from_list


class Product:
    """存储每一个商品信息"""

    # -------------------- nested ProductKey --------------------
    class ProductKey:
        """商品比较的键, 实现全序属性"""

        def __init__(self, sort_key: list):
            self._key = sort_key

        def key(self):
            """用于排序的 key"""
            return self._key

        def __hash__(self):
            """对转换为元组"""
            return hash(tuple(self.key()))

        # --------------- 设置比较逻辑: 从而实现全序属性 ---------------
        def __eq__(self, other):
            """是否相等"""
            if not isinstance(other, self.__class__):  # 类型要一致
                raise TypeError(f"Cannot compare {self.__class__.__name__} with {other.__class__.__name__}")
            my_key, other_key = self.key(), other.key()
            for me, you in zip(my_key, other_key):
                if me != you:
                    return False
            return True

        def __lt__(self, other):
            """比较大小 self < other"""
            if not isinstance(other, self.__class__):  # 类型要一致
                raise TypeError(f"Cannot compare {self.__class__.__name__} with {other.__class__.__name__}")
            my_key, other_key = self.key(), other.key()
            for me, you in zip(my_key, other_key):
                if me < you:
                    return True
                if me > you:
                    return False
            return False

    # -------------------- 商品 Product 类 --------------------
    def __init__(self, uid: int, name: str, sort_key: list, bucket: None):
        """
        初始化商品对象, 代表了唯一的一个商品
        :param uid: 唯一主键
        :param name: 商品名称
        :param sort_key: 用于排序比较的键 [price] or [price, popularity]
        :param bucket: 存储桶的地址
        """
        self._uid = uid  # 唯一主键
        self._name = name  # 商品名称
        self._key = self.ProductKey(sort_key)  # 用于排序比较的键 [price] or [price, popularity]
        self._bucket = bucket  # 存储桶地址

    @property
    def uid(self):
        return self._uid

    @property
    def key(self):
        return self._key

    @property
    def name(self):
        return self._name

    @property
    def bucket(self):
        return self._bucket

    def set_bucket(self, bucket: ProbeHashMap):
        """设置存储桶"""
        self._bucket = bucket

    def update_name(self, name):
        """设置新名"""
        self._name = name

    def key_element(self):
        key = self.key
        sort_key = key.key()
        return sort_key[0], sort_key[1]

    def __eq__(self, other):
        """比较 2 个商品, 完全由主键确定"""
        return self.uid == other.uid

    def __repr__(self):
        """返回对象属性"""
        return f"Product(uid={self.uid}, name={self.name}, sort_key={self.key.key()})"

    def __str__(self):
        return f"Product(uid={self.uid}, name={self.name}, sort_key={self.key.key()})"


class ProductService:
    """商品服务类"""

    def __init__(self):
        self.avl = AVLTreeMap()  # 存储 {ProductKey: {uid: Product, ...}, ...}
        self.uid_map = ProbeHashMap()  # {uid: Product 类}
        self.product_data_file = os.path.join(settings.DATA_DIR, '04products.csv')
        self._max_uid = 0
        self._n = 0

        # 读取数据
        with open(self.product_data_file, "r") as f:
            content = f.readlines()
            if len(content) != 0 and content[0] != '\n':
                for line in content:
                    if not line == '\n':
                        line = line.split(',')
                        line = [int(line[0]), line[1], -int(100 * float(line[2])), -int(line[3])]  # 价格扩大取整
                        if self._max_uid < line[0]:
                            self._max_uid = line[0]  # 找到目前最大主键
                        # 添加 Product 对象
                        self._add(uid=line[0], name=line[1], sort_key=[line[2], line[3]])

    def __len__(self):
        return self._n

    # -------------------- nonpublic method --------------------
    def _add(self, uid, name, sort_key: list):
        """插入, 当 uid 知时"""
        product = Product(uid, name, sort_key, bucket=None)
        self.uid_map[uid] = product  # 加入定位器

        key = product.key
        try:
            bucket = self.avl[key]  # 已有 key 相同的桶
            bucket[uid] = product  # 直接插入桶中
            product.set_bucket(bucket)  # 设置每个商品对应的桶
        except KeyError:
            # 未搜索到, 则创建新桶
            new_bucket = ProbeHashMap()
            new_bucket[uid] = product
            product.set_bucket(new_bucket)

            self.avl[key] = new_bucket  # 将新桶插入 AVL 树

        self._n += 1  # 实际商品数
        return product

    # -------------------- 增删改查 --------------------
    def add(self, name, sort_key: list):
        """普通插入商品, uid 自动生成"""
        uid = self._max_uid + 1
        product = self._add(uid, name, sort_key)
        self._max_uid += 1
        return product

    def update(self, uid, name, sort_key: list):
        """改变键 key, 先删后加, 若相同则不变"""
        product = self.uid_map[uid]

        product.update_name(name)  # 改名

        key = product.key  # ProductKey 类
        # 1. 比较 key 是否改变
        if key.key() == sort_key:
            return None
        # 2. 否则先删后加
        self.remove(uid)
        new = self.add(name, sort_key)
        return new.uid

    def remove(self, uid):
        """删除 uid 商品"""
        if uid not in self.uid_map:
            return False
        # 1. 寻找商品类和桶
        product = self.uid_map[uid]
        bucket = product.bucket

        # 2. 从桶中删除商品, 且从对照表中删除
        del bucket[uid]
        del self.uid_map[uid]

        # 3. 检查桶, 桶空则从 AVL 中删除
        if len(bucket) == 0:
            key = product.key
            del self.avl[key]

        self._n -= 1
        return product  # 返回被删除的商品

    def __getitem__(self, uid):
        """根据 uid 获取商品 Product 类"""
        if uid not in self.uid_map:
            raise KeyError(f"No such uid {uid}")
        return self.uid_map[uid]

    def get(self, uid, default=None):
        try:
            return self[uid]
        except KeyError:
            return default

    def __iter__(self):
        """迭代遍历, 按顺序返回 Product 类"""
        for bucket in self.avl.values():
            for product in bucket.values():
                yield product

    def search_name(self, pattern: str):
        """
        匹配 pattern 的 name 返回成功的 uid
        :param pattern: 匹配模式
        :return: 成功匹配的 uid 列表[uid, uid, ...]
        """
        # 提前准备空间存储, 减少摊销时间
        uid_list = [None] * len(self)
        name_list = [None] * len(self)
        # 存储 uid 和 name
        i = 0
        for uid, product in self.uid_map.items():
            uid_list[i] = uid
            name_list[i] = product.name
            i += 1
        match_index = find_all_from_list(pattern=pattern, texts=name_list, sep="*")  # 开始匹配
        return [uid_list[idx] for idx in match_index]  # 返回 uid 列表

    # -------------------- 查范围 --------------------
    def find_range(self, start, end):
        """按照 key 查找范围内的商品对象 start, end: ProductKey"""
        for k, v in self.avl.find_range(start, end):
            # k: ProductKey, v: {uid: Product, ...}
            for product in v.values():
                yield product

    def prize_between(self, prize1, prize2):
        """返回价格 [prize1, prize2]"""
        p1 = Product.ProductKey([-int(prize2 * 100)])
        p2 = Product.ProductKey([-int(prize1 * 100)])
        return self.find_range(p1, p2)

    # -------------------- 保存 --------------------
    def save(self):
        """保存到数据表"""
        writer = ""
        for product in self:
            price, popularity = product.key_element()
            writer += f"{product.uid},{product.name},{abs(round(price / 100, 2))},{abs(popularity)}\n"
        with open(self.product_data_file, "w") as f:
            f.write(writer)


# -------------------- 生成测试数据 --------------------
def random_name(length=10):
    """生成随机商品名称"""
    return ''.join(random.choices(string.ascii_letters, k=length))


def random_num(start=1, end=1000):
    """生成随机数字"""
    return random.randint(start, end)


if __name__ == '__main__':
    product_service = ProductService()
    N = 1000
    for i in range(N):
        product_name = random_name(length=10)
        price = -random_num(start=1000, end=10000)
        popularity = -random_num(start=100, end=10000)
        product_service.add(product_name, [price, popularity])

    product_service.save()
    # p1 = product_service.add("p1", [-1.1, 0])
    # product_service.add("p2.1", [-2.2, -1])
    # product_service.add("p2.2", [-2.2, 0])
    # product_service.add("p3", [-3.3, 0])
    # p4 = product_service.add("p4", [-4.4, 0])
    # product_service.add("p5", [-5.5, 0])

    # print(product_service[1])

    # del product_service[1]
    # print(product_service[2])

    # print("=" * 15)
    # for product in product_service.find_range(p4.key, p1.key):
    #     print(product)
    #
    # print("=" * 15)
    # for product in product_service.prize_between(-5, -1):
    #     print(product)
    #
    # # product_service.save()
    #
    # print("=" * 100)
    # for product in product_service:
    #     print(product)
    #
    # print("=" * 100)
    # uid_list = product_service.search_name("p2")
    # print(uid_list)
