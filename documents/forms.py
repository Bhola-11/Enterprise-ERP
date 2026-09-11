from django import forms
from .models import Document, Folder

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'folder', 'file', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'folder': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }
