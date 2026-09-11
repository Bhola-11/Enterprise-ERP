from django.urls import path
from . import views

app_name = 'fixed_assets_depr'

urlpatterns = [
    path('', views.assets_dashboard, name='dashboard'),
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/create/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/post-period/<int:period_id>/', views.asset_post_depreciation, name='post_period'),
    path('assets/<int:pk>/impairment/', views.impairment_create, name='impairment_create'),
    path('assets/<int:pk>/disposal/', views.disposal_create, name='disposal_create'),
]
