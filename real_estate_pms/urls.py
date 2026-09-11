from django.urls import path
from . import views

app_name = 'real_estate_pms'

urlpatterns = [
    path('', views.pms_dashboard, name='dashboard'),
    path('properties/', views.property_list, name='property_list'),
    path('units/', views.unit_list, name='unit_list'),
    path('units/create/', views.unit_create, name='unit_create'),
    path('leases/', views.lease_list, name='lease_list'),
    path('leases/create/', views.lease_create, name='lease_create'),
    path('leases/<int:pk>/', views.lease_detail, name='lease_detail'),
    path('work-orders/', views.work_order_list, name='work_order_list'),
    path('work-orders/create/', views.work_order_create, name='work_order_create'),
    path('rent-roll/', views.rent_roll_report, name='rent_roll_report'),
]
