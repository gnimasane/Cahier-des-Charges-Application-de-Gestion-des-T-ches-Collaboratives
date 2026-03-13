"""
Commande Django à exécuter manuellement ou via un planificateur (cron/Task Scheduler).

Usage :
  py manage.py send_deadline_alerts

Pour automatiser (Windows Task Scheduler) :
  Créer une tâche planifiée quotidienne qui exécute :
  "C:\\...\venv\Scripts\python.exe" manage.py send_deadline_alerts
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from tasks.models import Task
from tasks.email_utils import send_deadline_alert


class Command(BaseCommand):
    help = "Envoie des emails d'alerte pour les tâches dont la deadline approche."

    def handle(self, *args, **options):
        days = getattr(settings, 'DEADLINE_ALERT_DAYS', 2)
        now = timezone.now()
        threshold = now + timedelta(days=days)

        tasks_to_alert = Task.objects.filter(
            status__in=['a_faire', 'en_cours'],
            deadline__gte=now,
            deadline__lte=threshold,
            assigned_to__isnull=False,
        ).select_related('assigned_to', 'project')

        sent = 0
        errors = 0
        for task in tasks_to_alert:
            success = send_deadline_alert(task)
            if success:
                sent += 1
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Email envoyé → {task.assigned_to.email} pour '{task.title}'"
                ))
            else:
                errors += 1
                self.stdout.write(self.style.WARNING(
                    f"⚠️ Échec email pour '{task.title}'"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"\n📧 Résumé: {sent} emails envoyés, {errors} erreurs. "
            f"({tasks_to_alert.count()} tâches dans les {days} prochains jours)"
        ))
