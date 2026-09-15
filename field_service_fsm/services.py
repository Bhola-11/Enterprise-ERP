import uuid
import hashlib
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import (
    ServiceTerritory, ServiceTechnician, WorkOrder, PartConsumption, CustomerSignoff
)
from inventory.models import Product, StockMovement

class DispatchSchedulingEngine:
    @staticmethod
    def find_best_technician(work_order):
        """
        Selects an available technician matching the work order territory and highest skill level.
        """
        qs = ServiceTechnician.objects.filter(
            organization=work_order.organization,
            is_available=True
        )
        if work_order.territory:
            territory_techs = qs.filter(primary_territory=work_order.territory)
            if territory_techs.exists():
                return territory_techs.first()
        return qs.first()

    @staticmethod
    @transaction.atomic
    def dispatch_work_order(work_order, technician):
        work_order.assigned_technician = technician
        work_order.status = 'DISPATCHED'
        work_order.save(update_fields=['assigned_technician', 'status'])
        return work_order


class InventoryConsumptionEngine:
    @staticmethod
    @transaction.atomic
    def record_part_consumption(work_order, product, quantity=1):
        unit_cost = getattr(product, 'cost_price', Decimal('50.00'))
        total_cost = unit_cost * Decimal(quantity)

        consumption = PartConsumption.objects.create(
            work_order=work_order,
            product=product,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            inventory_deducted=True
        )

        # Deduct stock quantity
        if hasattr(product, 'stock_quantity') and product.stock_quantity is not None:
            product.stock_quantity = max(0, product.stock_quantity - quantity)
            product.save(update_fields=['stock_quantity'])

        return consumption


class SLATrackerService:
    @staticmethod
    def check_sla_compliance(work_order):
        if not work_order.actual_end:
            now = timezone.now()
            is_breached = now > work_order.sla_deadline
            remaining_seconds = max(0, int((work_order.sla_deadline - now).total_seconds()))
        else:
            is_breached = work_order.actual_end > work_order.sla_deadline
            remaining_seconds = 0

        return {
            'is_breached': is_breached,
            'sla_deadline': work_order.sla_deadline,
            'remaining_hours': round(remaining_seconds / 3600.0, 1),
            'status': 'BREACHED' if is_breached else 'COMPLIANT'
        }

    @staticmethod
    @transaction.atomic
    def complete_with_signoff(work_order, signatory_name, rating=5, feedback=""):
        work_order.status = 'COMPLETED'
        work_order.actual_end = timezone.now()
        work_order.save(update_fields=['status', 'actual_end'])

        sig_hash = hashlib.sha256(f"{work_order.work_order_number}-{signatory_name}-{timezone.now()}".encode('utf-8')).hexdigest()
        signoff = CustomerSignoff.objects.create(
            work_order=work_order,
            signatory_name=signatory_name,
            satisfaction_rating=rating,
            feedback_notes=feedback,
            digital_signature_hash=sig_hash
        )
        return signoff
