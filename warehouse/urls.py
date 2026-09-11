from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.warehouse_list, name='list'),
    path('add/', views.warehouse_create_or_edit, name='create'),
    path('<int:pk>/edit/', views.warehouse_create_or_edit, name='edit'),
    path('transfers/', views.transfer_list, name='transfer_list'),
    path('transfers/<int:pk>/complete/', views.transfer_complete, name='transfer_complete'),
]
