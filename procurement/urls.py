from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    path('evaluations/', views.vendor_evaluations_list, name='evaluations'),
]
