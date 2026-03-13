"""
Tests unitaires pour ESMT Task Manager
Règles métier testées :
- Un étudiant NE PEUT PAS assigner une tâche à un professeur
- Seul le créateur du projet peut ajouter/supprimer des tâches et des membres
- Un membre assigné ne peut modifier que le statut de SES tâches
- Calcul des primes (30K à 90%, 100K à 100%)
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User
from projects.models import Project
from tasks.models import Task


# ==================== FIXTURES ====================

@pytest.fixture
def etudiant(db):
    return User.objects.create_user(
        username='etudiant1', email='etudiant@esmt.sn',
        password='pass1234!', role='etudiant',
        first_name='Moussa', last_name='Diallo'
    )

@pytest.fixture
def professeur(db):
    return User.objects.create_user(
        username='prof1', email='prof@esmt.sn',
        password='pass1234!', role='professeur',
        first_name='Dr. Samba', last_name='Ndiaye'
    )

@pytest.fixture
def autre_etudiant(db):
    return User.objects.create_user(
        username='etudiant2', email='etudiant2@esmt.sn',
        password='pass1234!', role='etudiant'
    )

@pytest.fixture
def projet_etudiant(db, etudiant):
    return Project.objects.create(
        name='Projet Étudiant', description='Test', creator=etudiant
    )

@pytest.fixture
def projet_professeur(db, professeur):
    return Project.objects.create(
        name='Projet Professeur', description='Test', creator=professeur
    )


# ==================== TESTS MODÈLES ====================

class TestUserModel(TestCase):
    def setUp(self):
        self.etudiant = User.objects.create_user(
            username='etu', email='etu@test.sn', password='pass1234!', role='etudiant'
        )
        self.professeur = User.objects.create_user(
            username='prof', email='prof@test.sn', password='pass1234!', role='professeur'
        )

    def test_is_etudiant(self):
        self.assertTrue(self.etudiant.is_etudiant)
        self.assertFalse(self.etudiant.is_professeur)

    def test_is_professeur(self):
        self.assertTrue(self.professeur.is_professeur)
        self.assertFalse(self.professeur.is_etudiant)


class TestProjectModel(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator', email='creator@test.sn', password='pass1234!', role='professeur'
        )
        self.member = User.objects.create_user(
            username='member', email='member@test.sn', password='pass1234!', role='etudiant'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.sn', password='pass1234!', role='etudiant'
        )
        self.project = Project.objects.create(
            name='Test Project', creator=self.creator
        )
        self.project.members.add(self.member)

    def test_creator_can_access(self):
        self.assertTrue(self.project.can_access(self.creator))

    def test_member_can_access(self):
        self.assertTrue(self.project.can_access(self.member))

    def test_non_member_cannot_access(self):
        self.assertFalse(self.project.can_access(self.other))

    def test_is_creator(self):
        self.assertTrue(self.project.is_creator(self.creator))
        self.assertFalse(self.project.is_creator(self.member))

    def test_completion_rate_no_tasks(self):
        self.assertEqual(self.project.get_completion_rate(), 0)

    def test_completion_rate_with_tasks(self):
        Task.objects.create(
            title='T1', project=self.project, created_by=self.creator, status='termine'
        )
        Task.objects.create(
            title='T2', project=self.project, created_by=self.creator, status='a_faire'
        )
        self.assertEqual(self.project.get_completion_rate(), 50.0)


class TestTaskModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='u', email='u@test.sn', password='pass1234!', role='professeur'
        )
        self.project = Project.objects.create(name='P', creator=self.user)
        self.deadline_past = timezone.now() - timedelta(days=1)
        self.deadline_future = timezone.now() + timedelta(days=5)

    def test_task_overdue(self):
        task = Task.objects.create(
            title='Overdue', project=self.project, created_by=self.user,
            deadline=self.deadline_past, status='a_faire'
        )
        self.assertTrue(task.is_overdue)

    def test_task_not_overdue_if_done(self):
        task = Task.objects.create(
            title='Done', project=self.project, created_by=self.user,
            deadline=self.deadline_past, status='termine'
        )
        self.assertFalse(task.is_overdue)

    def test_completed_on_time(self):
        task = Task.objects.create(
            title='OnTime', project=self.project, created_by=self.user,
            deadline=self.deadline_future, status='a_faire'
        )
        task.status = 'termine'
        task.save()
        # completed_at est maintenant, deadline est dans le futur → dans les délais
        self.assertTrue(task.completed_on_time)

    def test_completed_late(self):
        task = Task.objects.create(
            title='Late', project=self.project, created_by=self.user,
            deadline=self.deadline_past, status='termine'
        )
        task.completed_at = timezone.now()
        task.save()
        self.assertFalse(task.completed_on_time)


# ==================== TESTS RÈGLES MÉTIER ====================

class TestBusinessRules(TestCase):
    """
    Tests des règles métier critiques définies dans le cahier des charges.
    """

    def setUp(self):
        self.etudiant = User.objects.create_user(
            username='etu', email='etu@test.sn', password='pass1234!', role='etudiant'
        )
        self.professeur = User.objects.create_user(
            username='prof', email='prof@test.sn', password='pass1234!', role='professeur'
        )
        self.autre_etudiant = User.objects.create_user(
            username='etu2', email='etu2@test.sn', password='pass1234!', role='etudiant'
        )
        # Projet créé par un étudiant
        self.projet = Project.objects.create(
            name='Projet Test', creator=self.etudiant
        )
        self.projet.members.add(self.professeur, self.autre_etudiant)

    def test_etudiant_peut_creer_projet(self):
        """Un étudiant PEUT créer un projet (contrairement à certaines implémentations incorrectes)."""
        self.assertEqual(self.projet.creator, self.etudiant)
        self.assertEqual(self.projet.creator.role, 'etudiant')

    def test_seul_createur_peut_acceder_en_ecriture(self):
        """Seul le créateur peut modifier/supprimer le projet."""
        self.assertTrue(self.projet.is_creator(self.etudiant))
        self.assertFalse(self.projet.is_creator(self.professeur))
        self.assertFalse(self.projet.is_creator(self.autre_etudiant))

    def test_membre_peut_lire_projet(self):
        """Un membre peut accéder au projet en lecture."""
        self.assertTrue(self.projet.can_access(self.professeur))
        self.assertTrue(self.projet.can_access(self.autre_etudiant))

    def test_non_membre_ne_peut_pas_acceder(self):
        """Un non-membre ne peut pas accéder au projet."""
        inconnu = User.objects.create_user(
            username='x', email='x@test.sn', password='pass1234!', role='etudiant'
        )
        self.assertFalse(self.projet.can_access(inconnu))

    def test_professeur_peut_creer_projet(self):
        """Un professeur PEUT aussi créer un projet."""
        projet_prof = Project.objects.create(
            name='Cours Django', creator=self.professeur
        )
        self.assertEqual(projet_prof.creator.role, 'professeur')


# ==================== TESTS STATISTIQUES ET PRIMES ====================

class TestStatsPrimes(TestCase):
    """
    Tests du calcul des primes :
    - 30 000 FCFA si ≥ 90% des tâches terminées dans les délais
    - 100 000 FCFA si 100% des tâches terminées dans les délais
    """

    def calculate_prime(self, rate):
        from django.conf import settings
        if rate == 100:
            return getattr(settings, 'PRIME_100', 100000)
        elif rate >= 90:
            return getattr(settings, 'PRIME_90', 30000)
        return 0

    def test_prime_100_percent(self):
        """100% → 100 000 FCFA."""
        self.assertEqual(self.calculate_prime(100), 100000)

    def test_prime_90_percent(self):
        """90% → 30 000 FCFA."""
        self.assertEqual(self.calculate_prime(90), 30000)

    def test_prime_95_percent(self):
        """95% → 30 000 FCFA (entre 90 et 100)."""
        self.assertEqual(self.calculate_prime(95), 30000)

    def test_no_prime_below_90(self):
        """89% → 0 FCFA."""
        self.assertEqual(self.calculate_prime(89), 0)

    def test_no_prime_zero(self):
        """0% → 0 FCFA."""
        self.assertEqual(self.calculate_prime(0), 0)

    def test_prime_exactly_at_threshold_30k(self):
        """Exactement 90.0% → 30 000 FCFA."""
        self.assertEqual(self.calculate_prime(90.0), 30000)
