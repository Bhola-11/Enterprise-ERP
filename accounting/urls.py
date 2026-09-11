from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    path('', views.accounting_dashboard, name='dashboard'),
    path('chart-of-accounts/', views.chart_of_accounts, name='chart_of_accounts'),
    path('chart-of-accounts/add/', views.account_create, name='account_create'),
    path('journal-entries/', views.journal_entries_list, name='journal_entries'),
    path('journal-entries/<int:pk>/', views.journal_entry_detail, name='journal_entry_detail'),
    path('reports/trial-balance/', views.trial_balance, name='trial_balance'),
    path('reports/profit-and-loss/', views.profit_and_loss, name='profit_and_loss'),
    path('reports/balance-sheet/', views.balance_sheet, name='balance_sheet'),
]
