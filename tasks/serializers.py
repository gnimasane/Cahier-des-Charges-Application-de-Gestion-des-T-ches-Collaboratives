from rest_framework import serializers
from .models import Task
from users.models import User
from users.serializers import UserSerializer


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    is_on_time = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'project_name', 'title', 'description',
            'deadline', 'status', 'priority', 'assigned_to', 'assigned_to_detail',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'completed_at', 'is_on_time'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'completed_at']

    def get_is_on_time(self, obj):
        return obj.is_completed_on_time()

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            return data

        creator = request.user
        assigned_to = data.get('assigned_to')

        # RÈGLE MÉTIER CRITIQUE: Un étudiant ne peut pas assigner un professeur
        if assigned_to and creator.is_etudiant and assigned_to.is_professeur:
            raise serializers.ValidationError(
                {"assigned_to": "Un étudiant ne peut pas assigner un professeur à une tâche."}
            )

        # Vérifier que assigned_to est membre du projet
        project = data.get('project') or (self.instance.project if self.instance else None)
        if assigned_to and project:
            allowed = list(project.members.all()) + [project.creator]
            if assigned_to not in allowed:
                raise serializers.ValidationError(
                    {"assigned_to": "Cet utilisateur n'est pas membre du projet."}
                )

        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer limité pour les membres (ne peuvent changer que le statut de LEURS tâches).
    """
    class Meta:
        model = Task
        fields = ['status']

    def validate(self, data):
        request = self.context.get('request')
        task = self.instance
        if not task:
            return data
        # Seul le créateur du projet OU la personne assignée peut modifier
        is_project_creator = (task.project.creator == request.user)
        is_assigned = (task.assigned_to == request.user)
        if not is_project_creator and not is_assigned:
            raise serializers.ValidationError(
                "Vous ne pouvez modifier que les tâches qui vous sont assignées."
            )
        return data


class TaskListSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'project', 'project_name', 'status', 'priority',
            'deadline', 'assigned_to', 'assigned_to_name', 'created_at', 'completed_at'
        ]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None
