from django.urls import path
from . import views

app_name = 'fleet'

urlpatterns = [
    path('', views.vehicle_list, name='list'),
    path('add/', views.vehicle_create, name='create'),
    path('<int:pk>/', views.vehicle_detail, name='detail'),
    path('fuel/add/', views.fuel_log_create, name='fuel_create'),
]
