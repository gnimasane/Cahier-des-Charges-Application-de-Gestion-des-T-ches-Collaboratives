from django import forms
from django.core.exceptions import ValidationError
from .models import Task
from users.models import User


class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        if self.project:
            if self.current_user and self.current_user.is_professeur:
                # Professeur: peut assigner à TOUS les étudiants (pas seulement membres)
                self.fields['assigned_to'].queryset = User.objects.filter(role='etudiant').order_by('last_name', 'first_name')
            else:
                # Étudiant: uniquement les étudiants membres du projet
                members_qs = User.objects.filter(
                    id__in=list(self.project.members.values_list('id', flat=True)) + [self.project.creator.id]
                ).filter(role='etudiant')
                self.fields['assigned_to'].queryset = members_qs

    class Meta:
        model = Task
        fields = ['title', 'description', 'deadline', 'status', 'priority', 'assigned_to']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        assigned_to = cleaned_data.get('assigned_to')
        if assigned_to and self.current_user and self.current_user.is_etudiant:
            if assigned_to.is_professeur:
                raise ValidationError("Un étudiant ne peut pas assigner un professeur à une tâche.")
        return cleaned_data


class TaskStatusForm(forms.ModelForm):
    """Formulaire limité pour les membres assignés (statut uniquement)."""
    class Meta:
        model = Task
        fields = ['status']
