from django.contrib.contenttypes.models import ContentType
from .models import WorkflowDefinition, WorkflowStage, WorkflowInstance, ApprovalAction
from notifications.models import notify_user
from audit.middleware import log_audit_event

class WorkflowEngine:
    @staticmethod
    def start_workflow(module_type, target_object, requester, amount=0.0, notes=''):
        try:
            workflow = WorkflowDefinition.objects.get(module_type=module_type, is_active=True)
        except WorkflowDefinition.DoesNotExist:
            return None

        first_stage = workflow.stages.order_by('step_number').first()
        content_type = ContentType.objects.get_for_model(target_object)

        instance = WorkflowInstance.objects.create(
            workflow=workflow,
            current_stage=first_stage,
            content_type=content_type,
            object_id=target_object.id,
            requester=requester,
            amount=amount,
            notes=notes,
            status='PENDING'
        )

        # Notify approver
        if first_stage and first_stage.specific_approver:
            notify_user(
                recipient=first_stage.specific_approver,
                title=f"Approval Required: {workflow.name}",
                message=f"Request #{instance.id} by {requester.get_full_name() or requester.email} for amount ${amount:,.2f} requires your review.",
                category='APPROVAL',
                priority='HIGH',
                link=f"/workflows/instances/{instance.id}/"
            )

        log_audit_event(requester, 'CREATE', 'WorkflowInstance', instance.id, str(instance), description=f"Initiated approval workflow: {workflow.name}")
        return instance

    @staticmethod
    def process_action(instance, actor, action_type, comments='', request=None):
        if instance.status != 'PENDING':
            return False, "This workflow instance is already closed."

        stage = instance.current_stage
        action = ApprovalAction.objects.create(
            instance=instance,
            stage=stage,
            actor=actor,
            action=action_type,
            comments=comments
        )

        if action_type == 'REJECT':
            instance.status = 'REJECTED'
            instance.save(update_fields=['status', 'updated_at'])
            
            # Update target object status if applicable
            obj = instance.content_object
            if hasattr(obj, 'status'):
                obj.status = 'REJECTED'
                obj.save(update_fields=['status'])

            notify_user(
                recipient=instance.requester,
                title=f"Workflow Rejected: {instance.workflow.name}",
                message=f"Your request was rejected by {actor.get_full_name() or actor.email}. Reason: {comments}",
                category='APPROVAL',
                priority='HIGH'
            )
            log_audit_event(actor, 'REJECT', 'WorkflowInstance', instance.id, str(instance), request=request, description=f"Workflow rejected: {comments}")
            return True, "Workflow rejected."

        elif action_type == 'APPROVE':
            # Check next stage
            next_stage = instance.workflow.stages.filter(step_number__gt=stage.step_number if stage else 0).order_by('step_number').first()
            if next_stage:
                instance.current_stage = next_stage
                instance.save(update_fields=['current_stage', 'updated_at'])
                if next_stage.specific_approver:
                    notify_user(
                        recipient=next_stage.specific_approver,
                        title=f"Next Stage Approval: {instance.workflow.name}",
                        message=f"Stage {next_stage.step_number} approval required for request #{instance.id}.",
                        category='APPROVAL',
                        priority='HIGH',
                        link=f"/workflows/instances/{instance.id}/"
                    )
                log_audit_event(actor, 'APPROVE', 'WorkflowInstance', instance.id, str(instance), request=request, description=f"Approved stage {stage.step_number}, moved to stage {next_stage.step_number}")
                return True, f"Approved! Moved to stage {next_stage.step_number}."
            else:
                instance.status = 'APPROVED'
                instance.current_stage = None
                instance.save(update_fields=['status', 'current_stage', 'updated_at'])
                
                # Update target object
                obj = instance.content_object
                if hasattr(obj, 'status'):
                    obj.status = 'APPROVED'
                    obj.save(update_fields=['status'])

                notify_user(
                    recipient=instance.requester,
                    title=f"Workflow Fully Approved: {instance.workflow.name}",
                    message=f"Your request #{instance.id} has been fully approved!",
                    category='APPROVAL',
                    priority='NORMAL'
                )
                log_audit_event(actor, 'APPROVE', 'WorkflowInstance', instance.id, str(instance), request=request, description="Workflow fully approved and resolved.")
                return True, "Workflow fully approved!"

        return False, "Unknown action."
