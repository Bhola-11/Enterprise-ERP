from django.contrib import admin
from .models import WorkflowDefinition, WorkflowStage, WorkflowInstance, ApprovalAction

class WorkflowStageInline(admin.TabularInline):
    model = WorkflowStage
    extra = 1

@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'module_type', 'is_active', 'auto_escalate_hours')
    inlines = [WorkflowStageInline]

class ApprovalActionInline(admin.TabularInline):
    model = ApprovalAction
    extra = 0
    readonly_fields = ('stage', 'actor', 'action', 'comments', 'timestamp')

@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'workflow', 'status', 'requester', 'amount', 'created_at')
    list_filter = ('status', 'workflow')
    inlines = [ApprovalActionInline]
