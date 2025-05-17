# 商业决策平台的智能数据管理系统 DSA-Project

> 《数据结构与算法导论》2025春季学期课程项目

**首先介绍如何下载并进行本地测试：**

1. 进入任意用于存放本项目的文件夹

```bash
cd <DIR>
```

2. 利用 `git` 工具远程克隆

```bash
git clone ...
```





## 1 项目介绍

### 1.1 项目背景

你是一家新兴的“数据驱动商业决策平台”的员工，公司要求你帮助设计其底层数据处理模块。你需要设计一个系统支撑平台的智能化运行，该系统存储的数据包括：

- 营销任务：每一条任务存储任务名称、紧急度、影响力；
- 一个表示客户之间关系的加权有向图：图中的每个点表示一个客户并存储客户名称；
- 所有商品的数据：每一条数据存储商品名称、价格、热度。

### 1.2 项目文件结构

本项目基于 `Python` 开发，为更好的展示效果，采用 `Django` 网页框架，开发了一款“数据驱动商业决策平台”网页雏形，项目文件结构见下：

```bash
tree ./ -L 1
BiDms/
├── BiDms
├── LICENSE
├── README.md		# 说明文档
├── core			# [核心功能实现]
├── data			# 存储数据文件
└── manage.py		# Django 
```

其中【核心功能】实现的代码见 `core` 库

```bash
tree ./core/ -L 1
core/
├── __init__.py
├── admin.py
├── apps.py
├── migrations
├── models.py
├── services		# [核心功能具体实现]
├── static			# 静态文件样式等, css & js
├── templates		# 页面 HTML
├── tests
├── tests.py
├── urls.py
└── views			# Django 视图函数, 实现前后端交互和后端逻辑
```

核心功能具体实现 `services` 结构

```bash
tree ./core/services -L 1
./core/services
├── __init__.py
├── data_structures				# [项目使用的所有数据结构, 从零实现]
├── readme.md					# 补充说明文档, 解释如何测试
├── task_service.py				# 1. 实现营销任务优先调度功能
├── task_service_plus.py		# 1*. 实现营销任务优先调度功能 PLUS
├── client_service.py			# 2*. 客户网络与影响力传播分析 PLUS
├── product_service.py			# 3. 商品数据检索
└── product_service_plus.py		# 3*. 商品数据检索 PLUS
```

本项目实现的各类数据结构 `data_structures`

```bash
tree ./core/services/data_structures
./core/services/data_structures
├── __init__.py
├── b_plus_tree.py			# B+ 树
├── b_tree.py				# B 树
├── b_tree_disk.py			# B 树, 磁盘 I/O 处理
├── graph.py				# 图
├── heap.py					# 堆
├── map.py					# 映射
├── search_tree.py			# 搜索树 (AVL 树等实现的有序映射)
├── test_data/					# 存储测试用数据
└── utils						# 更基础的类和数据结构
    ├── __init__.py
    ├── adaptable_heap_priority_queue.py		# 基于堆实现的优先级队列
    ├── array_stack.py							# 基于数组实现的栈
    ├── linked_binary_tree.py					# 基于双向链表实现的树
    ├── map_base.py								# 映射的基类 ADT
    └── pattern_matching.py						# 模式匹配
```





