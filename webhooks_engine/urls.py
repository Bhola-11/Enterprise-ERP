from django.urls import path
from . import views

app_name = 'webhooks_engine'

urlpatterns = [
    path('', views.webhook_dashboard, name='dashboard'),
    path('endpoints/', views.endpoint_list, name='endpoint_list'),
    path('endpoints/create/', views.endpoint_create, name='endpoint_create'),
    path('endpoints/<int:pk>/', views.endpoint_detail, name='endpoint_detail'),
    path('deliveries/', views.delivery_list, name='delivery_list'),
    path('deliveries/<int:pk>/retry/', views.delivery_retry, name='delivery_retry'),
]