from django.urls import path
from . import views

app_name = 'reconciliation'

urlpatterns = [
    path('', views.statement_list, name='statement_list'),
    path('upload/', views.statement_upload, name='statement_upload'),
    path('workbench/<int:statement_id>/', views.reconciliation_workbench, name='workbench'),

    path('rules/', views.rule_list, name='rule_list'),
    path('rules/create/', views.rule_create, name='rule_create'),

    # APIs
    path('api/statement/<int:statement_id>/auto-reconcile/', views.api_auto_reconcile, name='api_auto_reconcile'),
    path('api/line/<int:line_id>/adjust/', views.api_post_adjustment, name='api_post_adjustment'),
    path('api/line/<int:line_id>/match/', views.api_match_line, name='api_match_line'),
]
