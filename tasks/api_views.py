from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Task
from .serializers import TaskSerializer, TaskStatusUpdateSerializer, TaskListSerializer
from projects.models import Project


class IsProjectCreatorOrAssignedReadOnly(permissions.BasePermission):
    """
    RÈGLES:
    - Créateur du projet: CRUD complet sur les tâches
    - Membre assigné: peut uniquement modifier LE STATUT de SES tâches
    - Autres membres: lecture seule
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Lecture: créateur du projet ou membre du projet
        if request.method in permissions.SAFE_METHODS:
            return (
                obj.project.creator == user or
                user in obj.project.members.all()
            )
        # Modification complète: créateur du projet seulement
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # Exception: la personne assignée peut changer le statut
            if obj.project.creator == user:
                return True
            if obj.assigned_to == user:
                # Autorisé seulement pour PATCH sur le statut
                return request.method == 'PATCH'
            return False
        return False


class TaskListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskListSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        project_id = self.request.query_params.get('project')
        status_filter = self.request.query_params.get('status')
        assigned_filter = self.request.query_params.get('assigned_to')

        # Un utilisateur voit les tâches des projets où il est créateur ou membre
        from projects.models import Project
        accessible_projects = Project.objects.filter(creator=user) | Project.objects.filter(members=user)
        qs = Task.objects.filter(project__in=accessible_projects)

        if project_id:
            qs = qs.filter(project_id=project_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if assigned_filter:
            qs = qs.filter(assigned_to_id=assigned_filter)

        return qs.select_related('project', 'assigned_to', 'created_by')

    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        # RÈGLE: Seul le créateur du projet peut ajouter des tâches
        if project.creator != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le créateur du projet peut ajouter des tâches.")
        serializer.save(created_by=self.request.user)


class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsProjectCreatorOrAssignedReadOnly]

    def get_serializer_class(self):
        user = self.request.user
        obj = self.get_object()
        # Si c'est un membre assigné (pas le créateur du projet), serializer limité
        if obj.project.creator != user and obj.assigned_to == user:
            return TaskStatusUpdateSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        from projects.models import Project
        accessible_projects = Project.objects.filter(creator=user) | Project.objects.filter(members=user)
        return Task.objects.filter(project__in=accessible_projects)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        # RÈGLE: Seul le créateur du projet peut supprimer une tâche
        if task.project.creator != request.user:
            return Response(
                {"error": "Seul le créateur du projet peut supprimer des tâches."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        is_project_creator = (task.project.creator == user)
        is_assigned = (task.assigned_to == user)

        if not is_project_creator and not is_assigned:
            return Response(
                {"error": "Vous ne pouvez modifier que les tâches qui vous sont assignées."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Si membre assigné (non créateur), il ne peut changer QUE le statut
        if not is_project_creator and is_assigned:
            allowed_fields = set(request.data.keys())
            if not allowed_fields.issubset({'status'}):
                return Response(
                    {"error": "Vous pouvez uniquement modifier le statut de vos tâches."},
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().update(request, *args, **kwargs)


class AssignableUsersAPIView(APIView):
    """
    Retourne la liste des utilisateurs assignables à une tâche dans un projet.
    RÈGLE: Si le créateur de la tâche est un étudiant, les professeurs sont exclus.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        members = list(project.members.all()) + [project.creator]
        # Dédupliquer
        seen = set()
        unique_members = []
        for m in members:
            if m.id not in seen:
                seen.add(m.id)
                unique_members.append(m)

        # RÈGLE: Un étudiant ne peut pas voir les profs comme assignables
        if request.user.is_etudiant:
            unique_members = [m for m in unique_members if not m.is_professeur]

        from users.serializers import UserSerializer
        return Response(UserSerializer(unique_members, many=True).data)
