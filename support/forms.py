from django import forms
from .models import SupportTicket, TicketComment

class TicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['ticket_id', 'subject', 'customer', 'category', 'priority', 'assigned_to', 'description']
        widgets = {
            'ticket_id': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['comment', 'is_internal_note']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your reply or internal note here...'}),
            'is_internal_note': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
