from django.urls import path
from . import views

app_name = 'workflows'

urlpatterns = [
    path('instances/', views.workflow_instance_list, name='instance_list'),
    path('instances/<int:pk>/', views.workflow_instance_detail, name='instance_detail'),
    path('definitions/', views.workflow_definitions_list, name='definitions'),
]
