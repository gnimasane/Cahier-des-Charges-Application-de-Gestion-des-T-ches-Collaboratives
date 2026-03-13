from django.db import models
from users.models import User
from django.conf import settings


class PrimeEvaluation(models.Model):
    """Évaluation des primes pour les professeurs."""
    PERIODE_CHOICES = [
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
    ]

    professeur = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='evaluations',
        limit_choices_to={'role': 'professeur'}
    )
    periode = models.CharField(max_length=20, choices=PERIODE_CHOICES)
    annee = models.IntegerField()
    trimestre = models.IntegerField(null=True, blank=True, help_text="1, 2, 3 ou 4")
    total_tasks = models.IntegerField(default=0)
    tasks_on_time = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0)
    prime_montant = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['professeur', 'periode', 'annee', 'trimestre']
        ordering = ['-annee', '-trimestre']

    def __str__(self):
        return f"{self.professeur} - {self.periode} {self.annee}"

    def calculate_prime(self):
        if self.completion_rate == 100:
            return settings.PRIME_100
        elif self.completion_rate >= 90:
            return settings.PRIME_90
        return 0
