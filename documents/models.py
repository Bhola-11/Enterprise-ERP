from django.db import models
from django.conf import settings

class Folder(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

class DocumentTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Document(models.Model):
    title = models.CharField(max_length=200)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/')
    version = models.PositiveSmallIntegerField(default=1)
    file_type = models.CharField(max_length=50, default='PDF')
    file_size_kb = models.PositiveIntegerField(default=100)
    tags = models.ManyToManyField(DocumentTag, blank=True, related_name='documents')
    description = models.TextField(blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} (v{self.version})"

class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveSmallIntegerField()
    file = models.FileField(upload_to='document_versions/')
    change_summary = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.document.title} - Version {self.version_number}"
