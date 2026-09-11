from django.urls import path
from . import views

app_name = 'quality_control'

urlpatterns = [
    path('', views.qc_dashboard, name='dashboard'),
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/create/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('ncrs/', views.ncr_list, name='ncr_list'),
    path('ncrs/<int:pk>/', views.ncr_detail, name='ncr_detail'),
]
