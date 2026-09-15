from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q

from .models import AppraisalCycle, CompetencyFramework, AppraisalSubmission, ContinuousFeedbackNote
from .forms import AppraisalCycleForm, AppraisalSubmissionForm, ContinuousFeedbackNoteForm
from .services import AppraisalScoringEngine
from hr.models import Employee


@login_required
def dashboard(request):
    active_cycle = AppraisalCycle.objects.filter(status__in=['ACTIVE', 'IN_CALIBRATION']).first()
    cycle_analytics = AppraisalScoringEngine.get_cycle_analytics(active_cycle) if active_cycle else None

    total_cycles = AppraisalCycle.objects.count()
    recent_feedbacks = ContinuousFeedbackNote.objects.select_related('employee', 'giver')[:6]
    competencies = CompetencyFramework.objects.filter(is_active=True)

    context = {
        'active_cycle': active_cycle,
        'analytics': cycle_analytics,
        'total_cycles': total_cycles,
        'recent_feedbacks': recent_feedbacks,
        'competencies': competencies,
        'page_title': 'Performance Management & 360-Degree Appraisal Hub'
    }
    return render(request, 'performance_appraisal/dashboard.html', context)


@login_required
def cycle_list(request):
    cycles = AppraisalCycle.objects.annotate(subs_count=Count('submissions')).all()
    return render(request, 'performance_appraisal/cycle_list.html', {
        'cycles': cycles,
        'page_title': 'Appraisal Review Cycles'
    })


@login_required
def cycle_create(request):
    if request.method == 'POST':
        form = AppraisalCycleForm(request.POST)
        if form.is_valid():
            c = form.save()
            messages.success(request, f"Appraisal Cycle '{c.name}' created.")
            return redirect('performance_appraisal:cycle_detail', pk=c.id)
    else:
        form = AppraisalCycleForm()

    return render(request, 'performance_appraisal/cycle_form.html', {
        'form': form,
        'page_title': 'Create Appraisal Review Cycle'
    })


@login_required
def cycle_detail(request, pk):
    cycle = get_object_or_404(AppraisalCycle, pk=pk)
    submissions = cycle.submissions.select_related('employee', 'manager', 'employee__department').all()
    analytics = AppraisalScoringEngine.get_cycle_analytics(cycle)

    context = {
        'cycle': cycle,
        'submissions': submissions,
        'analytics': analytics,
        'page_title': f"Review Cycle: {cycle.name}"
    }
    return render(request, 'performance_appraisal/cycle_detail.html', context)


@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(AppraisalSubmission, pk=pk)

    if request.method == 'POST':
        form = AppraisalSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            score, band = AppraisalScoringEngine.calculate_composite_score(sub)
            messages.success(request, f"Appraisal for {sub.employee} calculated: Composite Score {score} ({band}).")
            return redirect('performance_appraisal:cycle_detail', pk=sub.cycle.id)
    else:
        form = AppraisalSubmissionForm(instance=submission)

    return render(request, 'performance_appraisal/submission_form.html', {
        'submission': submission,
        'form': form,
        'page_title': f"Appraisal Scorecard: {submission.employee.first_name} {submission.employee.last_name}"
    })


@login_required
def feedback_list(request):
    feedbacks = ContinuousFeedbackNote.objects.select_related('employee', 'giver').all()
    return render(request, 'performance_appraisal/feedback_list.html', {
        'feedbacks': feedbacks,
        'page_title': 'Continuous Feedback & 1-on-1 Journal'
    })


@login_required
def feedback_create(request):
    if request.method == 'POST':
        form = ContinuousFeedbackNoteForm(request.POST)
        if form.is_valid():
            f = form.save()
            messages.success(request, f"Feedback recorded for {f.employee}.")
            return redirect('performance_appraisal:feedback_list')
    else:
        form = ContinuousFeedbackNoteForm()

    return render(request, 'performance_appraisal/feedback_form.html', {
        'form': form,
        'page_title': 'Give Continuous Feedback / 1-on-1 Check-in'
    })
