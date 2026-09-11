from django.db import models
from django.conf import settings

class Company(models.Model):
    name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='United States')
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name

class Contact(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    is_primary_contact = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}" + (f" ({self.company.name})" if self.company else "")

class Campaign(models.Model):
    name = models.CharField(max_length=150)
    campaign_type = models.CharField(max_length=50, choices=[('EMAIL', 'Email Campaign'), ('SOCIAL', 'Social Media'), ('WEBINAR', 'Webinar'), ('TRADE_SHOW', 'Trade Show'), ('REFERRAL', 'Referral')])
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    expected_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Lead(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New Lead'),
        ('CONTACTED', 'Contacted'),
        ('QUALIFIED', 'Qualified'),
        ('UNQUALIFIED', 'Unqualified'),
        ('CONVERTED', 'Converted to Deal'),
    ]

    SOURCE_CHOICES = [
        ('WEBSITE', 'Website Inbound'),
        ('CAMPAIGN', 'Marketing Campaign'),
        ('REFERRAL', 'Client Referral'),
        ('COLD_CALL', 'Outbound Sales'),
        ('TRADE_SHOW', 'Conference/Expo'),
        ('OTHER', 'Other'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='WEBSITE')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    lead_score = models.IntegerField(default=50) # 0 to 100
    estimated_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-lead_score', '-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.company_name or 'Individual'})"

class Opportunity(models.Model):
    STAGE_CHOICES = [
        ('PROSPECTING', 'Prospecting (10%)'),
        ('QUALIFICATION', 'Qualification (25%)'),
        ('PROPOSAL', 'Proposal / Demo (50%)'),
        ('NEGOTIATION', 'Negotiation (80%)'),
        ('CLOSED_WON', 'Closed Won (100%)'),
        ('CLOSED_LOST', 'Closed Lost (0%)'),
    ]

    name = models.CharField(max_length=200) # e.g. "Acme Enterprise ERP Migration"
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    lead = models.OneToOneField(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='converted_opportunity')
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES, default='PROSPECTING')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    probability = models.PositiveSmallIntegerField(default=20) # 0 - 100%
    expected_close_date = models.DateField()
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Opportunities'
        ordering = ['-amount']

    def __str__(self):
        return f"{self.name} - ${self.amount:,.2f} ({self.get_stage_display()})"

    @property
    def weighted_revenue(self):
        return float(self.amount) * (self.probability / 100.0)

class Activity(models.Model):
    TYPE_CHOICES = [
        ('CALL', 'Phone Call'),
        ('MEETING', 'Meeting / Zoom'),
        ('EMAIL', 'Email'),
        ('TASK', 'Action Item / Task'),
        ('NOTE', 'Internal Note'),
    ]

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='NOTE')
    subject = models.CharField(max_length=200)
    details = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Activities'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.subject}"
