from django.urls import path
from . import views

app_name = 'logistics_3pl'

urlpatterns = [
    path('', views.logistics_dashboard, name='dashboard'),
    path('consignments/', views.consignment_list, name='consignment_list'),
    path('consignments/create/', views.consignment_create, name='consignment_create'),
    path('consignments/<int:pk>/', views.consignment_detail, name='consignment_detail'),
    path('consignments/<int:pk>/milestone/', views.consignment_add_milestone, name='consignment_add_milestone'),
    path('consignments/<int:pk>/awb/', views.consignment_awb_slip, name='consignment_awb_slip'),
    path('carriers/', views.carrier_list, name='carrier_list'),
    path('carriers/create/', views.carrier_create, name='carrier_create'),
    path('api/calculate-volumetric/', views.api_calculate_volumetric, name='api_calculate_volumetric'),
]
