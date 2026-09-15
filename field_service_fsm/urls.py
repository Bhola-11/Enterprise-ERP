from django.urls import path
from . import views

app_name = 'field_service_fsm'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('dispatch/', views.dispatch_board_view, name='dispatch_board'),
    path('work-orders/', views.work_order_list_view, name='work_order_list'),
    path('work-orders/new/', views.work_order_create_view, name='work_order_create'),
    path('work-orders/<int:pk>/', views.work_order_detail_view, name='work_order_detail'),
    path('work-orders/<int:pk>/consume-parts/', views.consume_parts_view, name='consume_parts'),
    path('work-orders/<int:pk>/signoff/', views.customer_signoff_view, name='customer_signoff'),
]
