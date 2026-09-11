from django.contrib import admin
from .models import Folder, DocumentTag, Document, DocumentVersion

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_by', 'created_at')

@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ('name',)

class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'folder', 'version', 'file_type', 'file_size_kb', 'uploaded_by', 'is_archived', 'created_at')
    list_filter = ('folder', 'is_archived')
    search_fields = ('title', 'description')
    inlines = [DocumentVersionInline]
