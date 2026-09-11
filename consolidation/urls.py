from django.urls import path
from . import views

app_name = 'consolidation'

urlpatterns = [
    path('', views.consolidation_dashboard, name='dashboard'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('run/', views.run_consolidation_wizard, name='run_wizard'),
    path('statements/<int:pk>/', views.statement_detail, name='statement_detail'),
    path('rates/', views.rates_list, name='rates_list'),
]