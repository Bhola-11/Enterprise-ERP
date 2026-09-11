from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Document, Folder, DocumentVersion
from .forms import DocumentForm, FolderForm
from audit.middleware import log_audit_event

@login_required
def document_vault(request):
    folders = Folder.objects.all()
    folder_id = request.GET.get('folder')
    documents = Document.objects.select_related('folder', 'uploaded_by').filter(is_archived=False)

    if folder_id:
        documents = documents.filter(folder_id=folder_id)

    paginator = Paginator(documents, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'documents/vault.html', {
        'folders': folders,
        'page_obj': page_obj,
        'selected_folder': folder_id,
    })

@login_required
def document_upload(request):
    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.uploaded_by = request.user
        doc.save()
        log_audit_event(request.user, 'CREATE', 'Document', doc.id, str(doc), request=request)
        messages.success(request, f"Document '{doc.title}' uploaded successfully!")
        return redirect('documents:vault')
    return render(request, 'documents/upload_form.html', {'form': form, 'title': 'Upload Document'})

@login_required
def folder_create(request):
    form = FolderForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        f = form.save(commit=False)
        f.created_by = request.user
        f.save()
        log_audit_event(request.user, 'CREATE', 'Folder', f.id, str(f), request=request)
        messages.success(request, f"Folder '{f.name}' created!")
        return redirect('documents:vault')
    return render(request, 'documents/folder_form.html', {'form': form, 'title': 'Create Folder'})
