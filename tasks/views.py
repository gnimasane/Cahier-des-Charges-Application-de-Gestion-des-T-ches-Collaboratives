from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Task
from .forms import TaskForm, TaskStatusForm
from .email_utils import send_task_assigned_notification
from projects.models import Project


@login_required
def task_list_view(request):
    user = request.user
    status_filter = request.GET.get('status', '')
    project_filter = request.GET.get('project', '')

    from projects.models import Project
    accessible_projects = list(Project.objects.filter(creator=user)) + list(Project.objects.filter(members=user))
    tasks = Task.objects.filter(project__in=accessible_projects).select_related('project', 'assigned_to')

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if project_filter:
        tasks = tasks.filter(project_id=project_filter)

    return render(request, 'tasks/list.html', {
        'tasks': tasks,
        'status_filter': status_filter,
        'projects': accessible_projects,
    })


@login_required
def task_create_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    # RÈGLE: Seul le créateur du projet peut ajouter des tâches
    if project.creator != request.user:
        messages.error(request, "Seul le créateur du projet peut ajouter des tâches.")
        return redirect('project-detail', pk=project_id)

    form = TaskForm(
        request.POST or None,
        project=project,
        current_user=request.user
    )
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.created_by = request.user
        task.save()
        # Notifier l'utilisateur assigné par email
        if task.assigned_to:
            send_task_assigned_notification(task)
        messages.success(request, "Tâche créée avec succès!")
        return redirect('project-detail', pk=project_id)

    return render(request, 'tasks/form.html', {
        'form': form,
        'project': project,
        'title': 'Nouvelle Tâche'
    })


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    user = request.user
    is_project_creator = (task.project.creator == user)
    is_assigned = (task.assigned_to == user)
    is_member = user in task.project.members.all()

    if not is_project_creator and not is_assigned and not is_member:
        messages.error(request, "Accès non autorisé.")
        return redirect('task-list')

    return render(request, 'tasks/detail.html', {
        'task': task,
        'is_project_creator': is_project_creator,
        'is_assigned': is_assigned,
    })


@login_required
def task_edit_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    user = request.user
    is_project_creator = (task.project.creator == user)
    is_assigned = (task.assigned_to == user)

    if not is_project_creator and not is_assigned:
        messages.error(request, "Vous ne pouvez modifier que les tâches qui vous sont assignées.")
        return redirect('task-detail', pk=pk)

    if is_project_creator:
        # Créateur du projet: formulaire complet
        form = TaskForm(
            request.POST or None,
            instance=task,
            project=task.project,
            current_user=request.user
        )
    else:
        # Membre assigné: statut uniquement
        form = TaskStatusForm(request.POST or None, instance=task)

    if request.method == 'POST' and form.is_valid():
        old_assigned = task.assigned_to
        updated_task = form.save()
        # Notifier par email si l'assignation a changé
        if is_project_creator and updated_task.assigned_to and updated_task.assigned_to != old_assigned:
            send_task_assigned_notification(updated_task)
        messages.success(request, "Tâche mise à jour!")
        return redirect('task-detail', pk=pk)

    return render(request, 'tasks/form.html', {
        'form': form,
        'task': task,
        'title': 'Modifier la Tâche',
        'is_status_only': not is_project_creator,
    })


@login_required
def task_delete_view(request, pk):
    task = get_object_or_404(Task, pk=pk)

    # RÈGLE: Seul le créateur du projet peut supprimer une tâche
    if task.project.creator != request.user:
        messages.error(request, "Seul le créateur du projet peut supprimer des tâches.")
        return redirect('task-detail', pk=pk)

    project_id = task.project.pk
    if request.method == 'POST':
        task.delete()
        messages.success(request, "Tâche supprimée.")
        return redirect('project-detail', pk=project_id)

    return render(request, 'tasks/confirm_delete.html', {'task': task})
