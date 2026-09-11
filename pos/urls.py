from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    # Terminal & Session management
    path('', views.terminal_list, name='terminal_list'),
    path('terminals/create/', views.terminal_create, name='terminal_create'),
    path('terminals/<int:pk>/edit/', views.terminal_update, name='terminal_update'),

    # Shift Session Actions
    path('terminal/<int:terminal_id>/open/', views.session_open, name='session_open'),
    path('session/<int:session_id>/close/', views.session_close, name='session_close'),
    path('session/<int:session_id>/detail/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/z-report/', views.z_report, name='z_report'),
    path('session/<int:session_id>/cash-move/', views.cash_transaction_create, name='cash_move'),

    # Cashier Terminal Register
    path('session/<int:session_id>/register/', views.register, name='register'),

    # Orders & Receipts
    path('orders/', views.order_history, name='order_history'),
    path('order/<int:order_id>/receipt/', views.order_receipt, name='order_receipt'),

    # Real-time POS Cashier APIs
    path('api/products/search/', views.api_product_search, name='api_product_search'),
    path('api/customer/<int:customer_id>/loyalty/', views.api_customer_loyalty, name='api_customer_loyalty'),
    path('api/coupon/validate/', views.api_validate_coupon, name='api_validate_coupon'),
    path('api/order/checkout/', views.api_process_order, name='api_process_order'),
]
