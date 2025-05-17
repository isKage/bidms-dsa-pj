from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from ..services import ClientService

client_service = ClientService()


@require_GET
def clients_view(request):
    # 获取所有节点数据
    nodes = []
    for uid in client_service.locators:
        nodes.append({
            'name': str(uid),
            'label': {
                'show': True,
                'formatter': str(client_service.uid_to_name[uid])
            },
        })

    # 获取所有边数据
    edges = []
    for edge in client_service.g.edges():
        u, v = edge.endpoints()
        edges.append({
            'source': str(u.element()),
            'target': str(v.element()),
            'label': {
                'show': True,
                'formatter': str(-edge.element())
            },
        })

    # 获取最短路/影响力列表
    table_data = []
    all_influence = client_service.all_influence()  # {Vertex: num/None}
    for u, infl in all_influence:
        uid = int(u.element())
        name = client_service.uid_to_name[uid]
        table_data.append({
            'uid': str(uid),
            'name': name,
            'influence': -infl if infl is not None else 'None',
        })

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'nodes': nodes, 'edges': edges})
    return render(request, 'client/clients.html', {'influences': table_data})


@require_GET
def clients_influence(request, uid, loop):
    if uid is None:
        return redirect('/clients/')
    loop = True if loop == 'loop' else False
    uid = int(uid)
    client_name = client_service.get_name(uid)
    influence, discovered_v, discovered_e = client_service.influence(uid, loop)

    # 获取所有节点数据
    nodes = []
    for t_uid in client_service.locators:
        nodes.append({
            'name': str(t_uid),
            'label': {
                'show': True,
                'formatter': str(client_service.uid_to_name[t_uid])
            },
            'itemStyle': {
                'color': 'pink' if client_service.locators[t_uid] in discovered_v else None,
            }
        })

    # 获取所有边数据
    edges = []
    for edge in client_service.g.edges():
        u, v = edge.endpoints()
        edges.append({
            'source': str(u.element()),
            'target': str(v.element()),
            'label': {
                'show': True,
                'formatter': str(-edge.element())
            },
            'lineStyle': {
                'color': 'orange' if edge in discovered_e else 'grey',
            }
        })

    # 获取最短路/影响力列表
    table_data = []
    all_influence = client_service.all_influence()  # {Vertex: num/None}
    for u, infl in all_influence:
        uid = int(u.element())
        name = client_service.uid_to_name[uid]
        table_data.append({
            'uid': str(uid),
            'name': name,
            'influence': -infl if infl is not None else 'None',
        })

    context = {
        'uid': uid,
        'name': client_name,
        'influence': influence,
        'influences': table_data,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'nodes': nodes, 'edges': edges})
    return render(request, 'client/clients.html', context)


@require_GET
def node_add(request):
    if request.GET.get('action') == 'save':
        # 处理添加新客户
        client_name = request.GET.get('name')
        if client_name:
            # 添加新节点
            new_uid = client_service.add(client_name)

            # 添加关系
            for key, value in request.GET.items():
                if key.startswith('relation_') and value:
                    existing_uid = int(key.split('_')[1])
                    weight = int(value)
                    client_service.add_relation(new_uid, existing_uid, weight)

            client_service.save()
            return redirect('/clients/')

    # 获取所有可连点
    clients = [(uid, client_service.uid_to_name[uid]) for uid in client_service.locators]

    return render(request, 'client/node_add.html', {
        'clients': clients
    })


@require_GET
def node_detail(request, uid):
    # 获取节点信息
    node = {
        'uid': uid,
        'name': client_service.uid_to_name[int(uid)]
    }

    # 获取相邻节点
    adjacent_nodes = []
    u = client_service.get(int(uid))  # Vertex 类
    if u:
        # 从 u 出射的边 outgoing
        for neighbor in client_service.g.neighbors(u):
            adjacent_nodes.append({
                'uid': str(neighbor.element()),
                'name': client_service.uid_to_name[neighbor.element()]
            })
        # 从 u 入射的边 ingoing
        for neighbor in client_service.g.neighbors(u, outgoing=False):
            adjacent_nodes.append({
                'uid': str(neighbor.element()),
                'name': client_service.uid_to_name[neighbor.element()]
            })

    # 获取不相邻节点
    adjacent_uid = {int(adj['uid']) for adj in adjacent_nodes}
    available_clients = []
    for i in client_service.locators:
        if i != int(uid) and i not in adjacent_uid:
            available_clients.append((i, client_service.uid_to_name[i]))  # [(uid, name), ...]

    # 处理编辑和删除操作
    action = request.GET.get('action')
    if action == 'edit':
        new_name = request.GET.get('name')
        if new_name:
            # new name
            client_service.uid_to_name[int(uid)] = new_name

            # new edge (relation)
            for key, value in request.GET.items():
                if key.startswith('new_relation_') and value:
                    target_uid = int(key.split('_')[2])
                    weight = int(value)
                    client_service.add_relation(int(uid), target_uid, weight)

            client_service.save()
            return redirect('/clients/')
    elif action == 'delete':
        client_service.remove(int(uid))
        client_service.save()
        return redirect('/clients/')

    return render(request, 'client/node_detail.html', {
        'node': node,
        'adjacent_nodes': adjacent_nodes,
        'available_clients': available_clients
    })


@require_GET
def edge_detail(request, source, target):
    # 获取边信息
    edge = {
        'source': source,
        'target': target,
        'weight': -client_service.get_relation(int(source), int(target))
    }

    # 处理编辑和删除操作
    action = request.GET.get('action')
    if action == 'edit':
        new_weight = request.GET.get('weight')
        if new_weight:
            client_service.update_relation(int(source), int(target), int(new_weight))
            client_service.only_save_graph()
            return redirect(f'/clients/')
    elif action == 'delete':
        client_service.remove_relation(int(source), int(target))
        client_service.only_save_graph()
        return redirect('/clients/')

    return render(request, 'client/edge_detail.html', {'edge': edge})
