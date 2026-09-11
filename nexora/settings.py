"""
Django settings for Nexora Enterprise OS.
Enterprise ERP & Business Operating System
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-nexora-enterprise-os-secure-key-2026-prod-grade'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',

    # Nexora Core Modules
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'organizations.apps.OrganizationsConfig',
    'dashboard.apps.DashboardConfig',
    'crm.apps.CrmConfig',
    'sales.apps.SalesConfig',
    'purchasing.apps.PurchasingConfig',
    'procurement.apps.ProcurementConfig',
    'inventory.apps.InventoryConfig',
    'warehouse.apps.WarehouseConfig',
    'accounting.apps.AccountingConfig',
    'hr.apps.HrConfig',
    'payroll.apps.PayrollConfig',
    'projects.apps.ProjectsConfig',
    'support.apps.SupportConfig',
    'assets.apps.AssetsConfig',
    'fleet.apps.FleetConfig',
    'manufacturing.apps.ManufacturingConfig',
    'documents.apps.DocumentsConfig',
    'workflows.apps.WorkflowsConfig',
    'notifications.apps.NotificationsConfig',
    'reports.apps.ReportsConfig',
    'audit.apps.AuditConfig',
    'api.apps.ApiConfig',
    'pos.apps.PosConfig',
    'taxation.apps.TaxationConfig',
    'reconciliation.apps.ReconciliationConfig',
    'healthcare.apps.HealthcareConfig',
    'logistics_3pl.apps.Logistics3plConfig',
    'education_sis.apps.EducationSisConfig',
    'real_estate_pms.apps.RealEstatePmsConfig',
    'hospitality_pms.apps.HospitalityPmsConfig',
    'mrp_planning.apps.MrpPlanningConfig',
    'quality_control.apps.QualityControlConfig',
    'subcontracting.apps.SubcontractingConfig',
    'api_gateway.apps.ApiGatewayConfig',
    'webhooks_engine.apps.WebhooksEngineConfig',
    'integrations_sdk.apps.IntegrationsSdkConfig',
    'consolidation.apps.ConsolidationConfig',
    'treasury_cash.apps.TreasuryCashConfig',
    'fixed_assets_depr.apps.FixedAssetsDeprConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'nexora.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.erp_global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'nexora.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'login'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
