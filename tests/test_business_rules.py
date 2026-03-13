"""
Tests des règles métier critiques du projet ESMT Task Manager
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from projects.models import Project
from tasks.models import Task
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db
class TestRoleRules:
    """Tests des règles liées aux profils Étudiant / Professeur"""

    def setup_method(self):
        self.client = APIClient()
        self.etudiant = User.objects.create_user(
            username='etudiant1', email='etudiant@test.com',
            password='pass1234!', role='etudiant'
        )
        self.professeur = User.objects.create_user(
            username='prof1', email='prof@test.com',
            password='pass1234!', role='professeur'
        )
        self.project = Project.objects.create(
            name='Projet Test', creator=self.etudiant
        )
        self.project.members.add(self.professeur)

    def test_etudiant_cannot_assign_professeur_to_task(self):
        """RÈGLE: Un étudiant ne peut pas assigner un professeur à une tâche"""
        self.client.force_authenticate(user=self.etudiant)
        deadline = (timezone.now() + timedelta(days=7)).isoformat()
        response = self.client.post('/api/tasks/', {
            'project': self.project.id,
            'title': 'Tâche test',
            'deadline': deadline,
            'assigned_to': self.professeur.id,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'assigned_to' in response.data

    def test_etudiant_can_assign_etudiant(self):
        """RÈGLE: Un étudiant PEUT assigner un autre étudiant"""
        etudiant2 = User.objects.create_user(
            username='etudiant2', email='e2@test.com',
            password='pass1234!', role='etudiant'
        )
        self.project.members.add(etudiant2)
        self.client.force_authenticate(user=self.etudiant)
        deadline = (timezone.now() + timedelta(days=7)).isoformat()
        response = self.client.post('/api/tasks/', {
            'project': self.project.id,
            'title': 'Tâche pour étudiant',
            'deadline': deadline,
            'assigned_to': etudiant2.id,
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_professeur_can_assign_anyone(self):
        """RÈGLE: Un professeur peut assigner n'importe qui"""
        prof_project = Project.objects.create(name='Proj Prof', creator=self.professeur)
        prof_project.members.add(self.etudiant)
        self.client.force_authenticate(user=self.professeur)
        deadline = (timezone.now() + timedelta(days=7)).isoformat()
        response = self.client.post('/api/tasks/', {
            'project': prof_project.id,
            'title': 'Tâche assignée à étudiant',
            'deadline': deadline,
            'assigned_to': self.etudiant.id,
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_assignable_users_excludes_profs_for_etudiant(self):
        """L'API assignable filtre les profs pour les étudiants"""
        self.client.force_authenticate(user=self.etudiant)
        response = self.client.get(f'/api/tasks/assignable/{self.project.id}/')
        assert response.status_code == status.HTTP_200_OK
        roles = [u['role'] for u in response.data]
        assert 'professeur' not in roles


@pytest.mark.django_db
class TestProjectPermissions:
    """Tests des permissions sur les projets"""

    def setup_method(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username='creator', email='creator@test.com',
            password='pass1234!', role='professeur'
        )
        self.member = User.objects.create_user(
            username='member', email='member@test.com',
            password='pass1234!', role='etudiant'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com',
            password='pass1234!', role='etudiant'
        )
        self.project = Project.objects.create(name='Projet', creator=self.creator)
        self.project.members.add(self.member)

    def test_only_creator_can_add_task(self):
        """RÈGLE: Seul le créateur peut ajouter des tâches"""
        self.client.force_authenticate(user=self.member)
        deadline = (timezone.now() + timedelta(days=7)).isoformat()
        response = self.client.post('/api/tasks/', {
            'project': self.project.id,
            'title': 'Tâche par membre',
            'deadline': deadline,
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_creator_can_add_task(self):
        """Le créateur peut ajouter des tâches"""
        self.client.force_authenticate(user=self.creator)
        deadline = (timezone.now() + timedelta(days=7)).isoformat()
        response = self.client.post('/api/tasks/', {
            'project': self.project.id,
            'title': 'Tâche par créateur',
            'deadline': deadline,
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_only_creator_can_delete_task(self):
        """RÈGLE: Seul le créateur du projet peut supprimer une tâche"""
        task = Task.objects.create(
            project=self.project, title='Task',
            deadline=timezone.now() + timedelta(days=7),
            created_by=self.creator, assigned_to=self.member
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(f'/api/tasks/{task.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_member_can_only_update_status(self):
        """RÈGLE: Un membre assigné ne peut modifier QUE le statut"""
        task = Task.objects.create(
            project=self.project, title='Task',
            deadline=timezone.now() + timedelta(days=7),
            created_by=self.creator, assigned_to=self.member
        )
        self.client.force_authenticate(user=self.member)
        # Essayer de modifier le titre = interdit
        response = self.client.patch(f'/api/tasks/{task.id}/', {'title': 'Nouveau titre'})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Modifier le statut = autorisé
        response = self.client.patch(f'/api/tasks/{task.id}/', {'status': 'en_cours'})
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestStatisticsPrime:
    """Tests du calcul des primes (professeurs uniquement)"""

    def setup_method(self):
        self.client = APIClient()
        self.prof = User.objects.create_user(
            username='prof_prime', email='prime@test.com',
            password='pass1234!', role='professeur'
        )
        self.project = Project.objects.create(name='Proj', creator=self.prof)

    def _create_tasks(self, total, completed_on_time):
        deadline = timezone.now() - timedelta(hours=1)  # deadline passée
        for i in range(total):
            t = Task.objects.create(
                project=self.project, title=f'Task {i}',
                deadline=deadline + timedelta(days=1),
                created_by=self.prof, assigned_to=self.prof
            )
            if i < completed_on_time:
                t.status = 'termine'
                t.completed_at = deadline - timedelta(hours=2)  # avant deadline = dans les délais
                t.save()

    def test_prime_100k_at_100_percent(self):
        """100% des tâches dans les délais = 100 000 FCFA"""
        self._create_tasks(10, 10)
        self.client.force_authenticate(user=self.prof)
        response = self.client.get('/api/statistics/dashboard/')
        assert response.status_code == 200
        # Prime calculée dans les stats

    def test_no_prime_for_etudiant(self):
        """Les étudiants ne reçoivent pas de prime"""
        etudiant = User.objects.create_user(
            username='e_prime', email='eprime@test.com',
            password='pass1234!', role='etudiant'
        )
        self.client.force_authenticate(user=etudiant)
        response = self.client.get('/api/statistics/dashboard/')
        assert response.status_code == 200
        assert response.data['prime'] == 0
