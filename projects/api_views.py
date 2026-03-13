from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Project
from .serializers import ProjectSerializer
from users.models import User
from users.serializers import UserSerializer


class ProjectListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Projets créés par l'utilisateur OU dans lesquels il est membre
        return Project.objects.filter(
            creator=user
        ).union(Project.objects.filter(members=user)).order_by('-created_at')

    def perform_create(self, serializer):
        # Tout utilisateur (étudiant ou professeur) peut créer un projet
        serializer.save(creator=self.request.user)


class ProjectDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(creator=user) | Project.objects.filter(members=user)

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        if project.creator != request.user:
            return Response(
                {"error": "Seul le créateur peut modifier ce projet."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.creator != request.user:
            return Response(
                {"error": "Seul le créateur peut supprimer ce projet."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class ProjectMembersAPIView(APIView):
    """Ajouter/retirer des membres - réservé au créateur du projet."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if not project.can_access(request.user):
            return Response({"error": "Accès interdit."}, status=403)
        members = list(project.members.all())
        return Response(UserSerializer(members, many=True).data)

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk, creator=request.user)
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
            project.members.add(user)
            return Response({"message": f"{user.username} ajouté au projet."})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur non trouvé."}, status=404)

    def delete(self, request, pk):
        project = get_object_or_404(Project, pk=pk, creator=request.user)
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
            project.members.remove(user)
            return Response({"message": f"{user.username} retiré du projet."})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur non trouvé."}, status=404)
