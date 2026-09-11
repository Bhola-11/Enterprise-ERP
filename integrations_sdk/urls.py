from django.urls import path
from . import views

app_name = 'integrations_sdk'

urlpatterns = [
    path('', views.marketplace_dashboard, name='marketplace'),
    path('connectors/create/', views.connector_create, name='connector_create'),
    path('connectors/<int:pk>/', views.connector_detail, name='connector_detail'),
    path('connectors/<int:pk>/sync/', views.connector_trigger_sync, name='connector_trigger_sync'),
    path('logs/', views.sync_log_list, name='sync_log_list'),
]