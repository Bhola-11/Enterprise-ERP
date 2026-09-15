from django.urls import path
from . import views

app_name = 'b2b_portal'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('catalog/', views.catalog_list_view, name='catalog'),
    path('quick-order/', views.quick_order_view, name='quick_order'),
    path('quotes/<int:pk>/', views.quote_detail_view, name='quote_detail'),
    path('orders/', views.order_history_view, name='order_history'),
    path('payments/', views.invoice_payment_view, name='invoice_payment'),
    path('settings/', views.account_settings_view, name='account_settings'),
]
