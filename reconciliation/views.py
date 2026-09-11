import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Sum, Q

from .models import (
    BankStatement, BankStatementLine, ReconciliationRule,
    ReconciliationSession
)
from .forms import BankStatementUploadForm, ReconciliationRuleForm
from .services import FuzzyReconciliationEngine
from accounting.models import BankAccount, JournalItem, Account


@login_required
def statement_list(request):
    statements = BankStatement.objects.select_related('bank_account', 'imported_by').all().order_by('-end_date')
    return render(request, 'reconciliation/statement_list.html', {
        'statements': statements,
        'page_title': 'Bank Statements & Electronic Feeds'
    })


@login_required
def statement_upload(request):
    if request.method == 'POST':
        form = BankStatementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            bank_acc = form.cleaned_data['bank_account']
            fmt = form.cleaned_data['statement_format']
            file_obj = request.FILES['statement_file']
            raw_content = file_obj.read()

            try:
                stmt = FuzzyReconciliationEngine.import_statement(
                    bank_account=bank_acc,
                    raw_content=raw_content,
                    statement_format=fmt,
                    user=request.user
                )
                messages.success(request, f"Statement imported with {stmt.total_lines_count} transactions. Running auto-reconciliation pass...")
                # Run auto-reconciliation immediately
                FuzzyReconciliationEngine.execute_auto_reconciliation(stmt)
                return redirect('reconciliation:workbench', statement_id=stmt.id)
            except Exception as e:
                messages.error(request, f"Failed to parse statement: {str(e)}")
    else:
        form = BankStatementUploadForm()

    return render(request, 'reconciliation/statement_upload.html', {
        'form': form,
        'page_title': 'Upload Electronic Bank Statement'
    })


@login_required
def reconciliation_workbench(request, statement_id):
    statement = get_object_or_404(
        BankStatement.objects.select_related('bank_account'),
        pk=statement_id
    )

    lines = statement.lines.select_related('matched_journal_item__journal_entry', 'matched_payment').all()

    # GL Candidate Items for manual pairing
    gl_account = statement.bank_account.gl_account if hasattr(statement.bank_account, 'gl_account') and statement.bank_account.gl_account else None
    unmatched_gl_items = JournalItem.objects.filter(
        journal_entry__status='POSTED'
    ).select_related('journal_entry', 'account').order_by('-journal_entry__date')[:50]

    if gl_account:
        unmatched_gl_items = unmatched_gl_items.filter(account=gl_account)

    contra_accounts = Account.objects.all().order_by('code')

    return render(request, 'reconciliation/workbench.html', {
        'statement': statement,
        'lines': lines,
        'unmatched_gl_items': unmatched_gl_items,
        'contra_accounts': contra_accounts,
        'page_title': f'Reconciliation Workbench - {statement.bank_account.bank_name}'
    })


@login_required
def rule_list(request):
    rules = ReconciliationRule.objects.select_related('contra_account').all()
    return render(request, 'reconciliation/rule_list.html', {
        'rules': rules,
        'page_title': 'Automated Reconciliation Rules'
    })


@login_required
def rule_create(request):
    if request.method == 'POST':
        form = ReconciliationRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()
            messages.success(request, f"Rule {rule.name} created successfully.")
            return redirect('reconciliation:rule_list')
    else:
        form = ReconciliationRuleForm()

    return render(request, 'reconciliation/rule_form.html', {
        'form': form,
        'page_title': 'Add Reconciliation Rule'
    })


# ---------------- Interactive Workbench JSON APIs ----------------

@login_required
@require_POST
def api_auto_reconcile(request, statement_id):
    statement = get_object_or_404(BankStatement, pk=statement_id)
    FuzzyReconciliationEngine.execute_auto_reconciliation(statement)
    return JsonResponse({
        'success': True,
        'reconciled_count': statement.reconciled_lines_count,
        'total_count': statement.total_lines_count,
        'status': statement.status
    })


@login_required
@require_POST
def api_post_adjustment(request, line_id):
    try:
        line = get_object_or_404(BankStatementLine, pk=line_id)
        data = json.loads(request.body)
        contra_account_id = data.get('contra_account_id')
        contra_account = get_object_or_404(Account, pk=contra_account_id)

        je = FuzzyReconciliationEngine.post_adjustment_entry(line, contra_account, user=request.user)
        return JsonResponse({
            'success': True,
            'entry_number': je.entry_number,
            'message': f'Adjustment entry {je.entry_number} posted and matched.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_POST
def api_match_line(request, line_id):
    try:
        line = get_object_or_404(BankStatementLine, pk=line_id)
        data = json.loads(request.body)
        journal_item_id = data.get('journal_item_id')
        ji = get_object_or_404(JournalItem, pk=journal_item_id)

        line.matched_journal_item = ji
        line.status = 'MANUALLY_MATCHED'
        line.match_confidence_score = 100
        line.match_rule_applied = f"Manual match with GL #{ji.journal_entry.entry_number}"
        line.save()

        stmt = line.statement
        stmt.reconciled_lines_count = stmt.lines.filter(status__in=['AUTO_MATCHED', 'MANUALLY_MATCHED']).count()
        if stmt.reconciled_lines_count == stmt.total_lines_count:
            stmt.status = 'RECONCILED'
        stmt.save()

        return JsonResponse({'success': True, 'message': 'Statement line reconciled successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
