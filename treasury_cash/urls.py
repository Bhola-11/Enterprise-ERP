from django.urls import path
from . import views

app_name = 'treasury_cash'

urlpatterns = [
    path('', views.treasury_dashboard, name='dashboard'),
    path('pools/', views.pool_list, name='pool_list'),
    path('pools/create/', views.pool_create, name='pool_create'),
    path('pools/<int:pk>/', views.pool_detail, name='pool_detail'),
    path('pools/<int:pk>/sweep/', views.pool_execute_sweep, name='pool_execute_sweep'),
    path('forecasts/', views.forecast_list, name='forecast_list'),
    path('hedging/', views.hedging_list, name='hedging_list'),
]