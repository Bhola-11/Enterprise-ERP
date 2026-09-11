from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ProcurementCategory, VendorEvaluation, SpendingLimit
from audit.middleware import log_audit_event

@login_required
def vendor_evaluations_list(request):
    evals = VendorEvaluation.objects.select_related('category', 'evaluated_by').all()
    categories = ProcurementCategory.objects.all()
    limits = SpendingLimit.objects.all()
    return render(request, 'procurement/evaluation_list.html', {
        'evaluations': evals,
        'categories': categories,
        'limits': limits,
    })
