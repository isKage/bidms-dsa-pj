from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods

from ..services import ProductService

# 全局 ProductService 实例, 避免重复读取数据
product_service = ProductService()


@require_http_methods(["GET", "POST"])
def products_view(request):
    context = {}

    # 处理 GET 请求, 获取 price 参数
    price1 = request.GET.get('price1')
    price2 = request.GET.get('price2')

    # plus 功能: 搜索匹配名字
    uid_list = None
    pattern = request.GET.get('pattern', '')
    if pattern != '':
        uid_list = product_service.search_name(pattern)

    # 获取所有商品或 price1 to price2 的商品
    products = []
    if price1 and price2:
        price1, price2 = float(price1), float(price2)
        for product in product_service.prize_between(price1, price2):
            products.append(product)
    else:
        for product in product_service:
            products.append(product)

    # 打包传递给前端的数据
    table_data = []
    for product in products:
        uid, product_name = product.uid, product.name

        # 加入 name 匹配限制
        if uid_list:
            if uid not in uid_list:
                continue
        price, popularity = product.key_element()
        table_data.append({
            'uid': uid,
            'product_name': product_name,
            'price': -round(price / 100, 2),
            'popularity': -popularity,
        })
    context['products'] = table_data  # 展示内容
    context['length'] = len(product_service)  # 总长度
    context['show_num'] = len(table_data)  # 最终展示

    return render(request, 'product/products.html', context)


@require_http_methods(["GET"])
def delete_product(request):
    # 处理删除商品
    uid = request.GET.get('uid')  # get uid

    # 1. 检查 uid 获取是否成功
    if not uid:  # 未获取到 uid
        return JsonResponse({'status': 'error', 'message': 'UID 不能为空'}, status=400)

    try:
        uid = int(uid)
    except ValueError:  # uid 不是整数
        return JsonResponse({'status': 'error', 'message': 'UID 必须是整数'}, status=400)

    if uid not in product_service.uid_map:
        return JsonResponse({'status': 'error', 'message': '商品不存在'}, status=404)

    # 2. 获取成功后, 进行删除
    result = product_service.remove(uid)
    if result:  # 删除成功, 保存到磁盘文件中
        product_service.save()  # 保存
        return JsonResponse({'status': 'success'})  # 向前端传回响应
    else:
        return JsonResponse({'status': 'error', 'message': '删除任务失败'}, status=400)


@require_http_methods(["GET", "POST"])
def product_detail_view(request, uid=None):
    context = {}

    # 1. 处理 GET 请求, 用于展示已有数据
    if request.method == 'GET':
        # uid 通过 url 传递
        if uid:
            # 获取任务详情
            product = product_service.get(uid)
            if not product:  # 未查询到
                return HttpResponseBadRequest("商品不存在")

            uid, product_name = product.uid, product.name
            price, popularity = product.key_element()
            # 获取成功后, 更新数据
            context.update({
                'uid': uid,
                'product_name': product_name,
                'price': -round(price / 100, 2),
                'popularity': -popularity,
                'is_edit': True
            })
        else:
            context.update({
                'is_edit': False
            })

    # 2. update & add 操作: 处理 POST 请求
    elif request.method == 'POST':
        product_name = request.POST.get('product_name', '').strip()
        price = request.POST.get('price', '').strip()
        popularity = request.POST.get('popularity', '').strip()

        # a 尝试获取, 检查是否成功
        if not all([product_name, price, popularity]):
            context['error'] = '不允许提交空白内容'
            return render(request, 'product/product_detail.html', context)

        price = float(price)
        popularity = int(popularity)
        try:
            # 正整数约束
            if price < 0 or popularity < 0:
                raise ValueError
        except ValueError:
            context['error'] = '价格和热度必须为正数'
            return render(request, 'product/product_detail.html', context)

        # b 获取成功
        if uid:
            if uid not in product_service.uid_map:
                context['error'] = '商品不存在'
                return render(request, 'product/product_detail.html', context)

            # 更新现有商品
            product_service.update(uid, product_name, [-int(price * 100), -popularity])
            product_service.save()
            return redirect('products')
        else:
            # 新增任务
            uid = product_service.add(product_name, [-int(price * 100), -popularity])
            if uid:
                product_service.save()
                return redirect('products')
            else:
                context['error'] = '添加商品失败'
                return render(request, 'product/product_detail.html', context)

    return render(request, 'product/product_detail.html', context)
