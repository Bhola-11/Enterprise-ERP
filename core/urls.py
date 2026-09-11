from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('search/', views.global_search, name='search'),
    path('settings/', views.system_settings_view, name='settings'),
]
