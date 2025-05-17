from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods

from ..services import TaskServicePlus

# 全局 TaskServicePlus 实例, 避免重复读取数据
task_service = TaskServicePlus()


@require_http_methods(["GET", "POST"])
def tasks_view_plus(request):
    context = {}

    # 处理 GET 请求, 获取 top k 参数
    k = request.GET.get('k', None)

    # 获取所有任务或 top k 任务
    if k is not None and k.isdigit() and int(k) < len(task_service):
        k = int(k)
        if k < len(task_service) // 2:  # k < n / 2
            tasks = task_service.nlargest_klogn(k)
        else:
            tasks = task_service.nlargest_nlogk(k)
        uid_k = [task[0] for task in tasks]
    else:
        tasks = task_service.all_tasks()  # 所有数据
        uid_k = []
    # tasks = [(uid, task_name, urgency, impact), ...]

    # 最终获取 k 个
    context['show_num'] = len(tasks)

    # 打包传递给前端的数据
    table_data = []
    for task in tasks:
        uid, task_name, urgency, impact = task
        table_data.append({
            'uid': uid,
            'task_name': task_name,
            'urgency': urgency,
            'impact': impact,
        })
    context['tasks'] = table_data  # 展示内容
    context['length'] = len(task_service)  # 总长度

    # 绘制关系图
    # 获取所有节点数据
    nodes = []
    for uid in task_service.locators:
        nodes.append({
            'name': str(uid),
            'label': {
                'show': True,
                'formatter': str(task_service.locators[uid].value()[1])
            },
            'itemStyle': {
                'color': 'pink' if uid in uid_k else None,
            }
        })

    # 获取所有边数据
    edges = []
    for edge in task_service.g.edges():
        u, v = edge.endpoints()
        edges.append({
            'source': str(u.element()),
            'target': str(v.element()),
            'label': {
                'show': False,
                # 'formatter': str(edge.element())
            },
        })

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'nodes': nodes, 'edges': edges})

    return render(request, 'task_plus/tasks.html', context)


@require_http_methods(["GET"])
def delete_task_plus(request):
    # 处理删除任务
    uid = request.GET.get('uid')  # get uid

    # 1. 检查 uid 获取是否成功
    if not uid:  # 未获取到 uid
        return JsonResponse({'status': 'error', 'message': 'UID 不能为空'}, status=400)

    try:
        uid = int(uid)
    except ValueError:  # uid 不是整数
        return JsonResponse({'status': 'error', 'message': 'UID 必须是整数'}, status=400)

    if uid not in task_service.locators:
        return JsonResponse({'status': 'error', 'message': '任务不存在'}, status=404)

    # 2. 获取成功后, 进行删除
    result = task_service.remove(uid)  # 删除
    if result:  # 删除成功, 保存到磁盘文件中
        task_service.save()  # 保存
        return JsonResponse({'status': 'success'})  # 向前端传回响应
    else:
        return JsonResponse({'status': 'error', 'message': '删除任务失败'}, status=400)


@require_http_methods(["GET", "POST"])
def task_detail_view_plus(request, uid=None):
    context = {}

    # 1. 处理 GET 请求, 用于展示已有数据
    if request.method == 'GET':
        # uid 通过 url 传递
        if uid:
            # 获取任务详情
            result = task_service.get(uid)
            if not result:  # 未查询到
                return HttpResponseBadRequest("任务不存在")

            _, (uid, task_name, urgency, impact) = result
            # 获取成功后, 更新数据
            context.update({
                'uid': uid,
                'task_name': task_name,
                'urgency': urgency,
                'impact': impact,
                'is_edit': True
            })
        else:
            context.update({
                'is_edit': False
            })

    # 2. update & add 操作: 处理 POST 请求
    elif request.method == 'POST':
        task_name = request.POST.get('task_name', '').strip()
        urgency = request.POST.get('urgency', '').strip()
        impact = request.POST.get('impact', '').strip()

        # a 尝试获取, 检查是否成功
        if not all([task_name, urgency, impact]):
            context['error'] = '不允许提交空白内容'
            return render(request, 'task_plus/task_detail.html', context)

        try:
            # 正整数约束
            urgency = int(urgency)
            impact = int(impact)
            if urgency <= 0 or impact <= 0:
                raise ValueError
        except ValueError:
            context['error'] = '紧急度和影响度必须是正整数'
            return render(request, 'task_plus/task_detail.html', context)

        # b 获取成功
        if uid:
            if uid not in task_service.locators:
                context['error'] = '任务不存在'
                return render(request, 'task_plus/task_detail.html', context)

            # 更新现有任务
            task_service.update(uid, task_name, urgency, impact)
            task_service.save()
            return redirect('tasks_plus')
        else:
            # 新增任务
            uid = task_service.add(task_name, urgency, impact)
            if uid:
                task_service.save()
                return redirect('tasks_plus')
            else:
                context['error'] = '添加任务失败'
                return render(request, 'task_plus/task_detail.html', context)

    return render(request, 'task_plus/task_detail.html', context)


def add_relation_view(request):
    if request.method == 'POST':
        uid = request.POST.get('uid')
        vid = request.POST.get('vid')
        if not uid or not vid:
            return JsonResponse({'status': 'error', 'message': '缺少参数'})

        try:
            success = task_service.add_relation(int(uid), int(vid))
            if success:
                task_service.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': '添加失败'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'})


def delete_relation_view(request):
    if request.method == 'POST':
        uid = request.POST.get('uid')
        vid = request.POST.get('vid')
        if not uid or not vid:
            return JsonResponse({'status': 'error', 'message': '缺少参数'})

        try:
            success = task_service.remove_relation(int(uid), int(vid))
            if success:
                task_service.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': '删除失败'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'})
