from django.urls import path
from . import views

app_name = 'api_gateway'

urlpatterns = [
    path('', views.gateway_dashboard, name='dashboard'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('keys/<int:pk>/revoke/', views.key_revoke, name='key_revoke'),
    path('policies/', views.policy_list, name='policy_list'),
    path('logs/', views.log_list, name='log_list'),

    # Gateway Public & Secured API Proxy
    path('api/v1/ping/', views.api_v1_gateway_ping, name='api_ping'),
    path('api/v1/inventory/catalog/', views.api_v1_inventory_catalog, name='api_inventory_catalog'),
    path('api/v1/orders/summary/', views.api_v1_orders_summary, name='api_orders_summary'),
]