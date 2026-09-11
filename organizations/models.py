from django.db import models

class Organization(models.Model):
    name = models.CharField(max_length=200, default='Nexora Global Technologies Inc.')
    legal_name = models.CharField(max_length=255, default='Nexora Global Enterprises LLC')
    tax_id = models.CharField(max_length=50, default='US-TX-987654321')
    registration_number = models.CharField(max_length=50, default='CORP-2024-8899')
    email = models.EmailField(default='contact@nexora.io')
    phone = models.CharField(max_length=30, default='+1 (800) 555-0199')
    website = models.URLField(default='https://www.nexora.io')
    currency = models.CharField(max_length=10, default='USD')
    currency_symbol = models.CharField(max_length=5, default='$')
    fiscal_year_start_month = models.PositiveSmallIntegerField(default=1)  # 1 = January
    logo = models.ImageField(upload_to='org_logos/', blank=True, null=True)
    address = models.CharField(max_length=255, default='100 Enterprise Boulevard, Suite 500')
    city = models.CharField(max_length=100, default='San Francisco')
    state = models.CharField(max_length=100, default='California')
    postal_code = models.CharField(max_length=20, default='94105')
    country = models.CharField(max_length=100, default='United States')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Branch(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    manager = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='United States')
    is_headquarters = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Branches'
        ordering = ['-is_headquarters', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Department(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    manager_name = models.CharField(max_length=100, blank=True, null=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('organization', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class CostCenter(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='cost_centers')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='cost_centers')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    budget_allocated = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    budget_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class FiscalYear(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='fiscal_years')
    title = models.CharField(max_length=50) # e.g. FY 2026-2027
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        status = 'Closed' if self.is_closed else 'Active'
        return f"{self.title} ({status})"

class TaxSetting(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='tax_settings')
    name = models.CharField(max_length=100) # Standard VAT, GST, Sales Tax
    rate = models.DecimalField(max_digits=5, decimal_places=2) # e.g. 18.00 %
    tax_code = models.CharField(max_length=30)
    is_compound = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.rate}%)"
