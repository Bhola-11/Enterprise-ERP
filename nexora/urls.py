"""
Nexora Enterprise OS URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Custom Admin Site Headers
admin.site.site_header = "Nexora Enterprise OS — Administration"
admin.site.site_title = "Nexora Enterprise ERP"
admin.site.index_title = "Enterprise Operations & Business Governance Portal"

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core Landing & Search
    path('', include('core.urls', namespace='core')),
    
    # Authentication & User Management
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Organization Management
    path('organizations/', include('organizations.urls', namespace='organizations')),
    
    # Executive Dashboard
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    
    # Core Enterprise Modules
    path('crm/', include('crm.urls', namespace='crm')),
    path('sales/', include('sales.urls', namespace='sales')),
    path('purchasing/', include('purchasing.urls', namespace='purchasing')),
    path('procurement/', include('procurement.urls', namespace='procurement')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('warehouse/', include('warehouse.urls', namespace='warehouse')),
    path('accounting/', include('accounting.urls', namespace='accounting')),
    path('hr/', include('hr.urls', namespace='hr')),
    path('payroll/', include('payroll.urls', namespace='payroll')),
    path('projects/', include('projects.urls', namespace='projects')),
    path('support/', include('support.urls', namespace='support')),
    path('assets/', include('assets.urls', namespace='assets')),
    path('fleet/', include('fleet.urls', namespace='fleet')),
    path('manufacturing/', include('manufacturing.urls', namespace='manufacturing')),
    path('documents/', include('documents.urls', namespace='documents')),
    path('workflows/', include('workflows.urls', namespace='workflows')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('audit/', include('audit.urls', namespace='audit')),
    path('pos/', include('pos.urls', namespace='pos')),
    path('taxation/', include('taxation.urls', namespace='taxation')),
    path('reconciliation/', include('reconciliation.urls', namespace='reconciliation')),
    path('healthcare/', include('healthcare.urls', namespace='healthcare')),
    path('logistics/', include('logistics_3pl.urls', namespace='logistics_3pl')),
    path('education/', include('education_sis.urls', namespace='education_sis')),
    path('real-estate/', include('real_estate_pms.urls', namespace='real_estate_pms')),
    path('hospitality/', include('hospitality_pms.urls', namespace='hospitality_pms')),
    path('mrp/', include('mrp_planning.urls', namespace='mrp_planning')),
    path('quality/', include('quality_control.urls', namespace='quality_control')),
    path('subcontracting/', include('subcontracting.urls', namespace='subcontracting')),
    path('gateway/', include('api_gateway.urls', namespace='api_gateway')),
    path('webhooks/', include('webhooks_engine.urls', namespace='webhooks_engine')),
    path('integrations/', include('integrations_sdk.urls', namespace='integrations_sdk')),
    path('consolidation/', include('consolidation.urls', namespace='consolidation')),
    path('treasury/', include('treasury_cash.urls', namespace='treasury_cash')),
    path('assets/depreciation/', include('fixed_assets_depr.urls', namespace='fixed_assets_depr')),
    path('succession/', include('succession_planning.urls', namespace='succession_planning')),
    path('performance/', include('performance_appraisal.urls', namespace='performance_appraisal')),
    path('rostering/', include('shifts_rostering.urls', namespace='shifts_rostering')),
    path('payroll-engine/', include('localized_payroll.urls', namespace='localized_payroll')),
    
    # REST API Layer
    path('api/v1/', include('api.urls', namespace='api_v1')),
    path('api/', include('api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
