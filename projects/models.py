from django.db import models
from users.models import User


class Project(models.Model):
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('en_pause', 'En pause'),
        ('termine', 'Terminé'),
        ('archive', 'Archivé'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # Tout utilisateur (étudiant ou professeur) peut créer un projet
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    members = models.ManyToManyField(User, related_name='member_projects', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='actif')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_creator(self, user):
        return self.creator == user

    def is_member(self, user):
        return self.members.filter(pk=user.pk).exists()

    def can_access(self, user):
        return self.is_creator(user) or self.is_member(user)

    def get_completion_rate(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter(status='termine').count()
        return round((completed / total) * 100, 1)
