from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project
from .forms import ProjectForm


@login_required
def project_list_view(request):
    user = request.user
    created = Project.objects.filter(creator=user)
    member_of = Project.objects.filter(members=user)
    return render(request, 'projects/list.html', {'created': created, 'member_of': member_of})


@login_required
def project_create_view(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.creator = request.user
        project.save()
        form.save_m2m()
        messages.success(request, "Projet créé!")
        return redirect('project-detail', pk=project.pk)
    return render(request, 'projects/form.html', {'form': form, 'title': 'Nouveau projet'})


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.can_access(request.user):
        messages.error(request, "Accès refusé.")
        return redirect('project-list')
    tasks = project.tasks.select_related('assigned_to').order_by('-created_at')
    return render(request, 'projects/detail.html', {'project': project, 'tasks': tasks})


@login_required
def project_edit_view(request, pk):
    project = get_object_or_404(Project, pk=pk, creator=request.user)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Projet mis à jour.")
        return redirect('project-detail', pk=project.pk)
    return render(request, 'projects/form.html', {'form': form, 'project': project, 'title': 'Modifier le projet'})


@login_required
def project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk, creator=request.user)
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Projet supprimé.")
        return redirect('project-list')
    return render(request, 'projects/confirm_delete.html', {'project': project})
