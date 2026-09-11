from django.urls import path
from . import views

app_name = 'mrp_planning'

urlpatterns = [
    path('', views.mrp_dashboard, name='dashboard'),
    path('mps/', views.mps_list, name='mps_list'),
    path('mps/create/', views.mps_create, name='mps_create'),
    path('run-wizard/', views.run_mrp_wizard, name='run_mrp_wizard'),
    path('runs/<int:pk>/', views.mrp_run_detail, name='mrp_run_detail'),
    path('safety-stock/', views.safety_stock_list, name='safety_stock_list'),
    path('safety-stock/create/', views.safety_stock_create, name='safety_stock_create'),
]
