from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .forms import RegisterForm, LoginForm, ProfileForm
from projects.models import Project
from tasks.models import Task
from django.utils import timezone


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            user_obj = User.objects.get(email=form.cleaned_data['email'])
            user = authenticate(request, username=user_obj.username, password=form.cleaned_data['password'])
        except User.DoesNotExist:
            user = None
        if user:
            login(request, user)
            if user.is_professeur:
                return redirect('dashboard-professeur')
            else:
                return redirect('dashboard-etudiant')
        messages.error(request, "Email ou mot de passe incorrect.")
    return render(request, 'users/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        login(request, user)
        if user.is_professeur:
            return redirect('dashboard-professeur')
        else:
            return redirect('dashboard-etudiant')
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profil mis à jour.")
        return redirect('profile')
    return render(request, 'users/profile.html', {'form': form})


@login_required
def dashboard_redirect(request):
    """Redirige vers le bon dashboard selon le rôle."""
    if request.user.is_professeur:
        return redirect('dashboard-professeur')
    return redirect('dashboard-etudiant')


@login_required
def dashboard_view(request):
    user = request.user
    # Projets accessibles
    my_projects = (Project.objects.filter(creator=user) | Project.objects.filter(members=user)).distinct()
    my_tasks = Task.objects.filter(assigned_to=user).select_related('project')

    total = my_tasks.count()
    a_faire = my_tasks.filter(status='a_faire').count()
    en_cours = my_tasks.filter(status='en_cours').count()
    termine = my_tasks.filter(status='termine').count()
    en_retard = sum(1 for t in my_tasks if t.is_overdue)
    on_time = sum(1 for t in my_tasks.filter(status='termine') if t.completed_on_time)
    rate = round((on_time / total * 100), 1) if total > 0 else 0

    prime = 0
    if user.is_professeur:
        if rate == 100:
            prime = 100000
        elif rate >= 90:
            prime = 30000

    context = {
        'my_projects': my_projects[:6],
        'recent_tasks': my_tasks.order_by('-updated_at')[:8],
        'stats': {
            'total': total,
            'a_faire': a_faire,
            'en_cours': en_cours,
            'termine': termine,
            'en_retard': en_retard,
            'rate': rate,
        },
        'prime': prime,
        'projects_count': my_projects.count(),
    }
    return render(request, 'dashboard.html', context)


@login_required
def dashboard_professeur_view(request):
    """Dashboard spécifique aux professeurs : projets créés, tâches, prime, membres."""
    user = request.user
    if not user.is_professeur:
        return redirect('dashboard-etudiant')


    from django.utils import timezone

    # Projets créés par ce professeur
    mes_projets = Project.objects.filter(creator=user).prefetch_related('tasks', 'members')
    total_projets = mes_projets.count()

    # Toutes les tâches dans ses projets
    from tasks.models import Task
    toutes_taches = Task.objects.filter(project__in=mes_projets).select_related('assigned_to', 'project')
    total_taches = toutes_taches.count()
    en_cours = toutes_taches.filter(status='en_cours').count()
    terminees = toutes_taches.filter(status='termine').count()
    a_faire = toutes_taches.filter(status='a_faire').count()
    en_retard = sum(1 for t in toutes_taches if t.is_overdue)

    # Taux et prime
    on_time = sum(1 for t in toutes_taches.filter(status='termine') if t.completed_on_time)
    rate = round((on_time / total_taches * 100), 1) if total_taches > 0 else 0
    prime = 0
    if rate == 100:
        prime = 100000
    elif rate >= 90:
        prime = 30000

    # Membres dans ses projets
    membres = set()
    for p in mes_projets:
        for m in p.members.all():
            membres.add(m)

    context = {
        'mes_projets': mes_projets[:6],
        'recent_tasks': toutes_taches.order_by('-updated_at')[:8],
        'membres': list(membres)[:8],
        'stats': {
            'total': total_taches,
            'a_faire': a_faire,
            'en_cours': en_cours,
            'termine': terminees,
            'en_retard': en_retard,
            'rate': rate,
        },
        'prime': prime,
        'projects_count': total_projets,
        'membres_count': len(membres),
    }
    return render(request, 'dashboard_professeur.html', context)


@login_required
def dashboard_etudiant_view(request):
    """Dashboard spécifique aux étudiants : tâches assignées, projets membres."""
    user = request.user
    if user.is_professeur:
        return redirect('dashboard-professeur')

    from tasks.models import Task
    from django.utils import timezone

    # Projets dont l'étudiant est membre ou créateur
    mes_projets = (Project.objects.filter(members=user) | Project.objects.filter(creator=user)).distinct()

    # Tâches : même logique que task_list_view (toutes les tâches des projets accessibles)
    mes_taches = Task.objects.filter(project__in=mes_projets).select_related('project', 'created_by', 'assigned_to')
    total = mes_taches.count()
    a_faire = mes_taches.filter(status='a_faire').count()
    en_cours = mes_taches.filter(status='en_cours').count()
    terminees = mes_taches.filter(status='termine').count()
    en_retard = sum(1 for t in mes_taches if t.is_overdue)
    urgentes = mes_taches.filter(status__in=['a_faire', 'en_cours'], priority='haute').count()

    context = {
        'mes_projets': mes_projets[:6],
        'mes_taches': mes_taches.order_by('deadline')[:8],
        'taches_urgentes': mes_taches.filter(status__in=['a_faire', 'en_cours'], priority='haute')[:5],
        'stats': {
            'total': total,
            'a_faire': a_faire,
            'en_cours': en_cours,
            'termine': terminees,
            'en_retard': en_retard,
            'urgentes': urgentes,
        },
        'projects_count': mes_projets.count(),
    }
    return render(request, 'dashboard_etudiant.html', context)
