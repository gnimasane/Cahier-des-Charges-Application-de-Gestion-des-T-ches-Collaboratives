from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime
from tasks.models import Task
from projects.models import Project
from users.models import User

PRIME_90 = 30000    # 30 000 FCFA pour >= 90%
PRIME_100 = 100000  # 100 000 FCFA pour 100%


def compute_user_stats(user, tasks_qs):
    total = tasks_qs.count()
    completed = tasks_qs.filter(status='termine').count()
    on_time = sum(1 for t in tasks_qs.filter(status='termine') if t.is_completed_on_time())
    in_progress = tasks_qs.filter(status='en_cours').count()
    todo = tasks_qs.filter(status='a_faire').count()

    completion_rate = round((completed / total * 100), 1) if total > 0 else 0

    # Prime uniquement pour les professeurs
    prime = 0
    if user.is_professeur:
        if completion_rate == 100:
            prime = PRIME_100
        elif completion_rate >= 90:
            prime = PRIME_90

    return {
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'todo': todo,
        'on_time': on_time,
        'completion_rate': completion_rate,
        'prime': prime,
        'prime_label': f"{prime:,} FCFA".replace(',', ' ') if prime > 0 else "Aucune prime",
    }


class MyStatsAPIView(APIView):
    """Statistiques personnelles de l'utilisateur connecté."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        period = request.query_params.get('period', 'all')  # all, trimestre, annuel
        now = timezone.now()

        tasks_qs = Task.objects.filter(assigned_to=user)

        if period == 'trimestre':
            # Trimestre en cours (3 mois)
            quarter_start = now.replace(month=((now.month - 1) // 3) * 3 + 1, day=1,
                                        hour=0, minute=0, second=0, microsecond=0)
            tasks_qs = tasks_qs.filter(deadline__gte=quarter_start)
        elif period == 'annuel':
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            tasks_qs = tasks_qs.filter(deadline__gte=year_start)

        stats = compute_user_stats(user, tasks_qs)
        stats['period'] = period
        stats['user_role'] = user.role

        # Répartition par projet
        project_stats = []
        for project in Project.objects.filter(
            id__in=tasks_qs.values_list('project_id', flat=True).distinct()
        ):
            p_tasks = tasks_qs.filter(project=project)
            p_total = p_tasks.count()
            p_done = p_tasks.filter(status='termine').count()
            project_stats.append({
                'id': project.id,
                'name': project.name,
                'total': p_total,
                'completed': p_done,
                'rate': round(p_done / p_total * 100, 1) if p_total > 0 else 0,
            })

        stats['projects'] = project_stats
        return Response(stats)


class TeamStatsAPIView(APIView):
    """
    Stats de tous les membres (accessible à tous).
    Affiche les primes pour les professeurs.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', 'all')
        now = timezone.now()

        professors = User.objects.filter(role='professeur')
        result = []

        for prof in professors:
            tasks_qs = Task.objects.filter(assigned_to=prof)

            if period == 'trimestre':
                quarter_start = now.replace(month=((now.month - 1) // 3) * 3 + 1, day=1,
                                            hour=0, minute=0, second=0, microsecond=0)
                tasks_qs = tasks_qs.filter(deadline__gte=quarter_start)
            elif period == 'annuel':
                year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                tasks_qs = tasks_qs.filter(deadline__gte=year_start)

            stats = compute_user_stats(prof, tasks_qs)
            result.append({
                'user_id': prof.id,
                'name': prof.get_full_name() or prof.username,
                'email': prof.email,
                'avatar_url': prof.get_avatar_url(),
                **stats,
            })

        # Tri par taux de completion décroissant
        result.sort(key=lambda x: x['completion_rate'], reverse=True)
        return Response({'period': period, 'professors': result})


class DashboardStatsAPIView(APIView):
    """Stats globales pour le tableau de bord."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        from projects.models import Project
        accessible_projects = Project.objects.filter(creator=user) | Project.objects.filter(members=user)

        my_tasks = Task.objects.filter(assigned_to=user)
        total_tasks = my_tasks.count()
        completed = my_tasks.filter(status='termine').count()
        in_progress = my_tasks.filter(status='en_cours').count()
        todo = my_tasks.filter(status='a_faire').count()
        completion_rate = round(completed / total_tasks * 100, 1) if total_tasks > 0 else 0

        prime = 0
        if user.is_professeur:
            if completion_rate == 100:
                prime = PRIME_100
            elif completion_rate >= 90:
                prime = PRIME_90

        # Tâches urgentes (deadline dans les 3 prochains jours)
        from datetime import timedelta
        urgent_deadline = timezone.now() + timedelta(days=3)
        urgent_tasks = my_tasks.filter(
            deadline__lte=urgent_deadline,
            status__in=['a_faire', 'en_cours']
        ).select_related('project')

        from tasks.serializers import TaskListSerializer
        return Response({
            'my_projects_count': accessible_projects.distinct().count(),
            'total_tasks': total_tasks,
            'completed': completed,
            'in_progress': in_progress,
            'todo': todo,
            'completion_rate': completion_rate,
            'prime': prime,
            'prime_label': f"{prime:,} FCFA".replace(',', ' ') if prime > 0 else None,
            'urgent_tasks': TaskListSerializer(urgent_tasks, many=True).data,
            'user_role': user.role,
        })
