 ESMT Task Manager

Application collaborative de gestion des tâches orientée ESMT pour les enseignants et étudiants.  
Chaque utilisateur peut créer des projets, y ajouter des tâches, les assigner à d'autres membres et suivre leur progression.  
Un système de statistiques trimestrielles et annuelles permet d’évaluer les performances des enseignants et d’attribuer des primes.

 🎯 Objectifs
- Faciliter la gestion des projets et des tâches en équipe
- Respecter les règles métier spécifiques aux rôles (Étudiant / Professeur)
- Offrir un suivi statistique et un système de primes pour les professeurs
- 
Règles métier implémentées
Un étudiant ne peut pas assigner un professeur à une tâche
→ Implémenté dans tasks/models.py (clean), tasks/serializers.py (validate), tasks/api_views.py (AssignableUsersAPIView), et Angular task-form.component.ts.

Seul le créateur du projet peut ajouter ou supprimer des tâches
→ Implémenté dans tasks/api_views.py (perform_create, destroy) et tasks/views.py.

Seul le créateur du projet peut gérer les membres
→ Implémenté dans projects/api_views.py (IsProjectCreator).

Les membres assignés ne peuvent modifier que le statut de leurs tâches
→ Implémenté dans tasks/api_views.py (update) et Angular task-form.component.ts (statusOnly).

Les primes (30K / 100K) sont réservées aux professeurs  
→ Implémenté dans statistics_app/api_views.py (compute_user_stats).

Deux profils sont disponibles : Étudiant et Professeur  
→ Implémenté dans users/models.py.

 Primes
- 30 000 FCFA : Professeur ayant complété ≥ 90% de ses tâches dans les délais  
- 100 000 FCFA: Professeur ayant complété 100% de ses tâches dans les délais  
- Les étudiants ne sont pas concernés par le système de primes

Stack technique
- Backend: Django 4.2, DRF, SimpleJWT, SQLite (dev) / PostgreSQL (prod)  
- Frontend: Angular 16, TypeScript  
- Auth : JWT tokens

-Installation rapide
 Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

-Frontend Angular
cd frontend-angular
npm install
ng serve
Accès

API Backend :
http://127.0.0.1:8000/api/

Application Web :
http://127.0.0.1:8000/

Admin Django :
http://127.0.0.1:8000/admin/

-API Routes principales
Auth
POST /api/users/register/ — Inscription (role: etudiant | professeur)

POST /api/users/login/ — Connexion

POST /api/auth/token/refresh/ — Refresh JWT

-Projects
GET/POST /api/projects/ — Liste / Créer

GET/PUT/DELETE /api/projects/:id/ — Détail / Modifier / Supprimer

POST/DELETE /api/projects/:id/members/ — Gérer les membres (créateur uniquement)

-Tasks
GET/POST /api/tasks/ — Liste / Créer (créateur du projet uniquement)

GET/PATCH/DELETE /api/tasks/:id/ — Détail / Modifier / Supprimer

GET /api/tasks/assignable/:project_id/ — Utilisateurs assignables

-Statistics
GET /api/statistics/dashboard/ — Stats du tableau de bord

GET /api/statistics/me/?period=all|trimestre|annuel — Mes stats

GET /api/statistics/team/?period=... — Stats des professeurs + primes

-Tests
bash
cd backend
pytest tests/ -v
