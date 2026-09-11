from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ORG_ADMIN', 'Organization Admin'),
        ('FINANCE_MANAGER', 'Finance Manager'),
        ('ACCOUNTANT', 'Accountant'),
        ('HR_MANAGER', 'HR Manager'),
        ('SALES_MANAGER', 'Sales Manager'),
        ('SALES_EXEC', 'Sales Executive'),
        ('PROCUREMENT_MANAGER', 'Procurement Manager'),
        ('WAREHOUSE_MANAGER', 'Warehouse Manager'),
        ('INVENTORY_MANAGER', 'Inventory Manager'),
        ('PROJECT_MANAGER', 'Project Manager'),
        ('SUPPORT_AGENT', 'Support Agent'),
        ('EMPLOYEE', 'Employee'),
    ]

    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='EMPLOYEE')
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.email})" if full_name else self.email

    @property
    def is_org_admin_or_super(self):
        return self.role in ['SUPER_ADMIN', 'ORG_ADMIN'] or self.is_superuser

    @property
    def is_finance_staff(self):
        return self.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'FINANCE_MANAGER', 'ACCOUNTANT']

    @property
    def is_hr_staff(self):
        return self.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'HR_MANAGER']

    @property
    def is_sales_staff(self):
        return self.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'SALES_MANAGER', 'SALES_EXEC']

    @property
    def is_warehouse_staff(self):
        return self.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'WAREHOUSE_MANAGER', 'INVENTORY_MANAGER']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='United States')
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(max_length=30, blank=True, null=True)
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    theme = models.CharField(max_length=20, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')

    def __str__(self):
        return f"Profile for {self.user.email}"

class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_records')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('SUCCESS', 'Success'), ('FAILED', 'Failed')], default='SUCCESS')

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Login Histories'

    def __str__(self):
        return f"{self.user.email} - {self.timestamp.strftime('%Y-%m-%d %H:%M')} - {self.status}"
