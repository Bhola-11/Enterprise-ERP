from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Supplier, PurchaseRequest, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GoodsReceiptItem
from .forms import SupplierForm, PurchaseOrderForm
from warehouse.models import Warehouse
from inventory.services import StockService
from workflows.engine import WorkflowEngine
from audit.middleware import log_audit_event

@login_required
def purchasing_dashboard(request):
    total_pos = PurchaseOrder.objects.count()
    pending_pos = PurchaseOrder.objects.filter(status='PENDING_APPROVAL').count()
    total_spend = PurchaseOrder.objects.filter(status__in=['APPROVED', 'RECEIVED', 'BILLED']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    suppliers_count = Supplier.objects.filter(is_active=True).count()

    recent_pos = PurchaseOrder.objects.select_related('supplier', 'created_by').order_by('-order_date')[:6]
    suppliers = Supplier.objects.order_by('-rating')[:5]

    return render(request, 'purchasing/dashboard.html', {
        'total_pos': total_pos,
        'pending_pos': pending_pos,
        'total_spend': total_spend,
        'suppliers_count': suppliers_count,
        'recent_pos': recent_pos,
        'suppliers': suppliers,
    })

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    search = request.GET.get('q')
    if search:
        suppliers = suppliers.filter(Q(name__icontains=search) | Q(email__icontains=search) | Q(city__icontains=search))

    paginator = Paginator(suppliers, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'purchasing/supplier_list.html', {'page_obj': page_obj})

@login_required
def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        supp = form.save()
        log_audit_event(request.user, 'CREATE', 'Supplier', supp.id, str(supp), request=request)
        messages.success(request, f'Supplier {supp.name} added successfully!')
        return redirect('purchasing:supplier_list')
    return render(request, 'purchasing/supplier_form.html', {'form': form, 'title': 'Add Supplier'})

@login_required
def po_list(request):
    pos = PurchaseOrder.objects.select_related('supplier', 'created_by').all()
    status_filter = request.GET.get('status')
    if status_filter:
        pos = pos.filter(status=status_filter)

    paginator = Paginator(pos, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'purchasing/po_list.html', {
        'page_obj': page_obj,
        'statuses': PurchaseOrder.STATUS_CHOICES,
        'selected_status': status_filter,
    })

@login_required
def po_detail(request, pk):
    po = get_object_or_404(PurchaseOrder.objects.select_related('supplier', 'created_by'), pk=pk)
    items = po.items.select_related('product').all()
    grns = po.receipt_notes.select_related('warehouse', 'received_by').all()
    warehouses = Warehouse.objects.filter(is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'submit_approval':
            po.status = 'PENDING_APPROVAL'
            po.save(update_fields=['status'])
            WorkflowEngine.start_workflow('PURCHASE_ORDER', po, request.user, amount=float(po.total_amount), notes=f"PO #{po.po_number}")
            messages.success(request, f'Purchase Order #{po.po_number} submitted for multi-tier approval.')
            return redirect('purchasing:po_detail', pk=pk)

        elif action == 'create_grn':
            wh_id = request.POST.get('warehouse')
            wh = get_object_or_404(Warehouse, id=wh_id)
            grn_num = f"GRN-{po.po_number}-{po.receipt_notes.count() + 1}"

            grn = GoodsReceiptNote.objects.create(
                grn_number=grn_num,
                purchase_order=po,
                warehouse=wh,
                receipt_date=request.POST.get('receipt_date') or po.order_date,
                received_by=request.user,
                notes=request.POST.get('notes', '')
            )

            # Receive all PO items into stock
            for itm in items:
                GoodsReceiptItem.objects.create(grn=grn, product=itm.product, quantity_received=itm.quantity)
                StockService.record_movement(
                    product=itm.product,
                    movement_type='PURCHASE_RECEIPT',
                    quantity=itm.quantity,
                    unit_cost=itm.unit_price,
                    reference_number=f"PO-{po.po_number}",
                    warehouse_name=wh.name,
                    user=request.user,
                    notes=f"Received via GRN #{grn_num}"
                )

            po.status = 'RECEIVED'
            po.save(update_fields=['status'])
            log_audit_event(request.user, 'CREATE', 'GoodsReceiptNote', grn.id, str(grn), request=request, description="Received items into inventory warehouse.")
            messages.success(request, f"Goods Receipt Note #{grn_num} created and stock updated!")
            return redirect('purchasing:po_detail', pk=pk)

    return render(request, 'purchasing/po_detail.html', {
        'po': po,
        'items': items,
        'grns': grns,
        'warehouses': warehouses,
    })
