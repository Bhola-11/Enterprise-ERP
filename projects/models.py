from django.db import models
from django.conf import settings
from hr.models import Employee
from crm.models import Company

class Project(models.Model):
    STATUS_CHOICES = [
        ('PLANNING', 'Planning Phase'),
        ('ACTIVE', 'Active / In Progress'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True) # e.g. PRJ-2026-01
    client = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    project_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='managed_projects')
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    progress_percentage = models.PositiveSmallIntegerField(default=0) # 0 - 100
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"[{self.code}] {self.name} ({self.get_status_display()})"

class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=150)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.project.code} - {self.title}"

class Task(models.Model):
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('IN_REVIEW', 'In Review / QA'),
        ('DONE', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=200)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    due_date = models.DateField(blank=True, null=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', 'due_date']

    def __str__(self):
        return f"{self.project.code} | {self.title} ({self.status})"

class Timesheet(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='timesheets')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='timesheets')
    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    description = models.CharField(max_length=255)
    is_billable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.hours} hrs on {self.task.title}"
