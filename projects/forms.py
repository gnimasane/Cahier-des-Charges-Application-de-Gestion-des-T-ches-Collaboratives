from django import forms
from .models import Project
from users.models import User


class ProjectForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple, label="Membres"
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'start_date', 'end_date', 'members']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
