from rest_framework import serializers
from .models import Project
from users.serializers import UserSerializer
from users.models import User


class ProjectSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all(),
        source='members', required=False
    )
    completion_rate = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'creator', 'members', 'member_ids',
                  'status', 'start_date', 'end_date', 'completion_rate', 'task_count',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']

    def get_completion_rate(self, obj):
        return obj.get_completion_rate()

    def get_task_count(self, obj):
        return obj.tasks.count()

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        project = Project.objects.create(**validated_data)
        project.members.set(members)
        return project

    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if members is not None:
            instance.members.set(members)
        return instance
