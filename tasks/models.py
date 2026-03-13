"""
RÈGLES MÉTIER:
- Un étudiant NE PEUT PAS assigner un professeur à une tâche
- Seul le créateur du projet peut ajouter/supprimer des tâches
- Un membre assigné peut uniquement modifier SES propres tâches
- La prime (30K/100K) concerne uniquement les professeurs
"""
from django.db import models
from django.core.exceptions import ValidationError
from users.models import User
from projects.models import Project


class Task(models.Model):
    STATUS_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]
    PRIORITY_CHOICES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='a_faire')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='moyenne')
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tâche'
        verbose_name_plural = 'Tâches'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"

    def clean(self):
        """RÈGLE: Un étudiant ne peut pas assigner un professeur à une tâche."""
        if self.assigned_to_id and self.created_by_id:
            try:
                assignee = User.objects.get(pk=self.assigned_to_id)
                creator = User.objects.get(pk=self.created_by_id)
                if creator.is_etudiant and assignee.is_professeur:
                    raise ValidationError(
                        "Un étudiant ne peut pas assigner un professeur à une tâche."
                    )
            except User.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.status == 'termine' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'termine':
            self.completed_at = None
        super().save(*args, **kwargs)

    def is_completed_on_time(self):
        if self.status == 'termine' and self.completed_at and self.deadline:
            return self.completed_at <= self.deadline
        return False

    @property
    def is_overdue(self):
        from django.utils import timezone
        if not self.deadline:
            return False
        return self.status != 'termine' and self.deadline < timezone.now()

    @property
    def completed_on_time(self):
        return self.is_completed_on_time()


