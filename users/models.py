from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ETUDIANT = 'etudiant'
    ROLE_PROFESSEUR = 'professeur'
    ROLE_CHOICES = [
        (ROLE_ETUDIANT, 'Étudiant'),
        (ROLE_PROFESSEUR, 'Professeur'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ETUDIANT)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_professeur(self):
        return self.role == self.ROLE_PROFESSEUR

    @property
    def is_etudiant(self):
        return self.role == self.ROLE_ETUDIANT

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/img/default-avatar.png'
