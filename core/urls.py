from django.urls import path
import core.views as views

urlpatterns = [
    # tasks
    path('tasks/', views.tasks_view, name='tasks'),
    path('tasks/delete/', views.delete_task, name='delete_task'),
    path('tasks/add/', views.task_detail_view, name='add_task'),
    path('tasks/detail/<int:uid>/', views.task_detail_view, name='edit_task'),

    # tasks/plus
    path('tasks/plus/', views.tasks_view_plus, name='tasks_plus'),
    path('tasks/plus/delete/', views.delete_task_plus, name='delete_task_plus'),
    path('tasks/plus/add/', views.task_detail_view_plus, name='add_task_plus'),
    path('tasks/plus/detail/<int:uid>/', views.task_detail_view_plus, name='edit_task_plus'),
    path('tasks/plus/add/relation/', views.add_relation_view, name='add_relation'),
    path('tasks/plus/delete/relation/', views.delete_relation_view, name='delete_relation'),


    # clients
    path('clients/', views.clients_view, name='clients'),
    path('clients/node_detail/<str:uid>/', views.node_detail, name='node_detail'),
    path('clients/edge_detail/<str:source>/<str:target>/', views.edge_detail, name='edge_detail'),
    path('clients/node_add/', views.node_add, name='node_add'),
    path('clients/influence/<str:uid>/<str:loop>', views.clients_influence, name='influence'),

    # products
    path('products/', views.products_view, name='products'),
    path('products/delete/', views.delete_product, name='delete_product'),
    path('products/add/', views.product_detail_view, name='add_product'),
    path('products/detail/<int:uid>/', views.product_detail_view, name='edit_product'),
]
