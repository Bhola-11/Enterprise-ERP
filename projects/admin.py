from django.contrib import admin
from .models import Project, Milestone, Task, Timesheet

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'project_manager', 'budget', 'status', 'priority', 'progress_percentage')
    list_filter = ('status', 'priority')
    search_fields = ('code', 'name')
    inlines = [MilestoneInline, TaskInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'status', 'priority', 'due_date')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'project__name')

@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ('employee', 'task', 'date', 'hours', 'is_billable')
    list_filter = ('date', 'is_billable')
