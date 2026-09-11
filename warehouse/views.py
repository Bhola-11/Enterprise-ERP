from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Warehouse, Zone, Bin, StockTransfer, StockTransferItem
from .forms import WarehouseForm, StockTransferForm
from inventory.services import StockService
from audit.middleware import log_audit_event

@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.select_related('branch').all()
    return render(request, 'warehouse/warehouse_list.html', {'warehouses': warehouses})

@login_required
def warehouse_create_or_edit(request, pk=None):
    wh = get_object_or_404(Warehouse, pk=pk) if pk else None
    form = WarehouseForm(request.POST or None, instance=wh)
    if request.method == 'POST' and form.is_valid():
        w = form.save()
        action = 'UPDATE' if wh else 'CREATE'
        log_audit_event(request.user, action, 'Warehouse', w.id, str(w), request=request)
        messages.success(request, f'Warehouse {w.name} saved successfully!')
        return redirect('warehouse:list')
    return render(request, 'warehouse/warehouse_form.html', {'form': form, 'warehouse': wh})

@login_required
def transfer_list(request):
    transfers = StockTransfer.objects.select_related('source_warehouse', 'destination_warehouse', 'created_by').all()
    paginator = Paginator(transfers, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'warehouse/transfer_list.html', {'page_obj': page_obj})

@login_required
def transfer_complete(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if transfer.status == 'COMPLETED':
        messages.warning(request, 'This transfer has already been completed.')
        return redirect('warehouse:transfer_list')

    if request.method == 'POST':
        for item in transfer.items.all():
            # Deduct from source
            StockService.record_movement(
                product=item.product,
                movement_type='TRANSFER_OUT',
                quantity=item.quantity,
                reference_number=f"TR-{transfer.transfer_number}",
                warehouse_name=transfer.source_warehouse.name,
                user=request.user,
                notes=f"Transfer to {transfer.destination_warehouse.name}"
            )
            # Add to destination
            StockService.record_movement(
                product=item.product,
                movement_type='TRANSFER_IN',
                quantity=item.quantity,
                reference_number=f"TR-{transfer.transfer_number}",
                warehouse_name=transfer.destination_warehouse.name,
                user=request.user,
                notes=f"Transfer from {transfer.source_warehouse.name}"
            )

        transfer.status = 'COMPLETED'
        transfer.save(update_fields=['status'])
        log_audit_event(request.user, 'UPDATE', 'StockTransfer', transfer.id, str(transfer), request=request, description="Completed warehouse stock transfer.")
        messages.success(request, f"Transfer #{transfer.transfer_number} completed and stock updated.")
        return redirect('warehouse:transfer_list')

    return render(request, 'warehouse/transfer_complete_confirm.html', {'transfer': transfer})
