from django.urls import path
from . import views

app_name = 'performance_appraisal'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cycles/', views.cycle_list, name='cycle_list'),
    path('cycles/create/', views.cycle_create, name='cycle_create'),
    path('cycles/<int:pk>/', views.cycle_detail, name='cycle_detail'),
    path('submissions/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('feedback/create/', views.feedback_create, name='feedback_create'),
]
