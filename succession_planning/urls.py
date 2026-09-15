from django.urls import path
from . import views

app_name = 'succession_planning'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nine-box/', views.nine_box_matrix, name='nine_box_matrix'),
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:pk>/', views.role_detail, name='role_detail'),
    path('talent/', views.talent_list, name='talent_list'),
    path('talent/calibrate/', views.talent_edit, name='talent_create'),
    path('talent/<int:employee_id>/calibrate/', views.talent_edit, name='talent_edit'),
]
