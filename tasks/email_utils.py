"""
Utilitaires d'envoi d'emails pour ESMT TaskManager.
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone


STYLE = """
  body{margin:0;padding:0;background:#f0f7ff;font-family:'Segoe UI',Arial,sans-serif;}
  .wrap{max-width:580px;margin:0 auto;padding:32px 16px;}
  .header{border-radius:12px 12px 0 0;padding:28px 32px;text-align:center;}
  .header h1{color:white;margin:0;font-size:22px;font-weight:700;}
  .header p{color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px;}
  .body{background:#ffffff;border:1.5px solid #dbeafe;border-top:none;border-radius:0 0 12px 12px;padding:28px 32px;}
  .greeting{color:#0c2340;font-size:15px;margin-bottom:8px;}
  .message{color:#2c5282;font-size:14px;line-height:1.6;margin-bottom:18px;}
  .info-box{border-radius:10px;padding:18px 20px;margin:18px 0;}
  .info-box h2{margin:0 0 12px;font-size:15px;}
  table{width:100%;border-collapse:collapse;}
  td{padding:5px 0;font-size:13px;vertical-align:top;}
  td:first-child{color:#7a94b0;width:110px;}
  td:last-child{color:#0c2340;font-weight:500;}
  .footer{color:#7a94b0;font-size:11px;text-align:center;margin-top:20px;}
  .urgent{color:#dc2626;font-weight:700;}
  .warning{color:#d97706;font-weight:700;}
"""


def _html_wrap(header_color, header_icon, header_title, body_html):
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"/><style>{STYLE}</style></head>
<body>
<div class="wrap">
  <div class="header" style="background:{header_color};">
    <h1>{header_icon} {header_title}</h1>
    <p>ESMT TaskManager — Plateforme Collaborative</p>
  </div>
  <div class="body">
    {body_html}
    <p class="footer">— ESMT TaskManager · École Supérieure Multinationale des Télécommunications</p>
  </div>
</div>
</body>
</html>"""


def send_task_assigned_notification(task):
    """Notifie l'utilisateur qu'une tache lui a ete assignee."""
    if not task.assigned_to or not task.assigned_to.email:
        return False

    prenom = task.assigned_to.get_full_name() or task.assigned_to.username
    projet = task.project.name
    deadline_str = task.deadline.strftime('%d/%m/%Y a %H:%M') if task.deadline else 'Non definie'

    subject = f"Nouvelle tache assignee : {task.title}"

    text_body = f"""Bonjour {prenom},

Une nouvelle tache vient de vous etre assignee dans le projet "{projet}".

Tache : {task.title}
Description : {task.description or 'Aucune description'}
Deadline : {deadline_str}
Priorite : {task.get_priority_display()}
Statut : {task.get_status_display()}

Connectez-vous sur ESMT TaskManager pour consulter les details.

Bon courage !
-- L'equipe ESMT TaskManager
"""

    desc_html = f"<p style='color:#2c5282;font-size:13px;margin:0 0 12px;'>{task.description}</p>" if task.description else ""

    body_html = f"""
    <p class="greeting">Bonjour <strong>{prenom}</strong>,</p>
    <p class="message">
      Une nouvelle tache vient de vous etre assignee dans le projet
      <strong style="color:#0ea5e9;">{projet}</strong>.
      Prenez-en connaissance et organisez votre travail pour respecter la deadline.
    </p>
    <div class="info-box" style="background:#f0f9ff;border:1.5px solid #bae6fd;border-left:4px solid #0ea5e9;">
      <h2 style="color:#0c2340;">{task.title}</h2>
      {desc_html}
      <table>
        <tr><td>Projet</td><td>{projet}</td></tr>
        <tr><td>Deadline</td><td class="warning">{deadline_str}</td></tr>
        <tr><td>Priorite</td><td>{task.get_priority_display()}</td></tr>
        <tr><td>Statut</td><td>{task.get_status_display()}</td></tr>
      </table>
    </div>
    <p class="message">
      N'oubliez pas de mettre a jour le statut de votre tache au fur et a mesure de votre avancement.
    </p>
"""

    html_body = _html_wrap(
        "linear-gradient(135deg,#0ea5e9,#38bdf8)",
        "Nouvelle Tache Assignee", "", body_html
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[task.assigned_to.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] send_task_assigned_notification: {e}")
        return False


def send_deadline_alert(task):
    """Alerte l'utilisateur assigne quand la deadline approche ou est depassee."""
    if not task.assigned_to or not task.assigned_to.email:
        return False

    prenom = task.assigned_to.get_full_name() or task.assigned_to.username
    projet = task.project.name
    deadline_str = task.deadline.strftime('%d/%m/%Y a %H:%M') if task.deadline else 'Non definie'

    now = timezone.now()
    if not task.deadline:
        return False

    delta = task.deadline - now
    days_left = delta.days
    is_overdue = delta.total_seconds() < 0

    if is_overdue:
        jours_retard = abs(days_left)
        subject = f"RETARD : Votre tache \"{task.title}\" est en retard !"
        alerte_txt = f"ATTENTION : votre tache est en retard de {jours_retard} jour(s). Vous devez la finaliser immediatement et contacter le responsable du projet."
        alerte_html = f'<p class="message" style="background:#fee2e2;border-radius:8px;padding:12px 16px;border-left:4px solid #dc2626;"><strong class="urgent">RETARD DE {jours_retard} JOUR(S)</strong><br/>Votre tache est en retard. Finalisez-la immediatement et signalez votre situation au responsable du projet.</p>'
        header_color = "linear-gradient(135deg,#dc2626,#ef4444)"
        header_icon = "RETARD"
        conseil = "Contactez immediatement le responsable du projet, expliquez votre situation et soumettez votre travail des que possible."

    elif days_left == 0:
        subject = f"URGENT : La deadline de \"{task.title}\" est aujourd'hui !"
        alerte_txt = "URGENT : La deadline de cette tache est AUJOURD'HUI. Finalisez votre travail avant la fin de la journee."
        alerte_html = '<p class="message" style="background:#fff7ed;border-radius:8px;padding:12px 16px;border-left:4px solid #d97706;"><strong class="warning">DEADLINE AUJOURD\'HUI</strong><br/>Vous devez finaliser cette tache et mettre a jour son statut avant la fin de la journee.</p>'
        header_color = "linear-gradient(135deg,#d97706,#f59e0b)"
        header_icon = "URGENT"
        conseil = "Ne tardez plus. Terminez la tache et passez son statut a Termine des que possible."

    else:
        subject = f"Rappel deadline : \"{task.title}\" dans {days_left} jour(s)"
        alerte_txt = f"Rappel : il vous reste {days_left} jour(s) pour finaliser cette tache."
        alerte_html = f'<p class="message" style="background:#f0f9ff;border-radius:8px;padding:12px 16px;border-left:4px solid #0ea5e9;">Il vous reste <strong style="color:#0ea5e9;">{days_left} jour(s)</strong> pour finaliser cette tache. Organisez-vous pour la terminer a temps.</p>'
        header_color = "linear-gradient(135deg,#0ea5e9,#0284c7)"
        header_icon = "Rappel Deadline"
        conseil = "Planifiez votre temps et mettez a jour le statut de la tache regulierement pour informer votre equipe."

    text_body = f"""Bonjour {prenom},

{alerte_txt}

Tache : {task.title}
Projet : {projet}
Deadline : {deadline_str}
Priorite : {task.get_priority_display()}
Statut actuel : {task.get_status_display()}

Conseil : {conseil}

Connectez-vous sur ESMT TaskManager pour mettre a jour le statut de votre tache.

-- L'equipe ESMT TaskManager
"""

    body_html = f"""
    <p class="greeting">Bonjour <strong>{prenom}</strong>,</p>
    {alerte_html}
    <div class="info-box" style="background:#fff7ed;border:1.5px solid #fed7aa;border-left:4px solid #d97706;">
      <h2 style="color:#0c2340;">{task.title}</h2>
      <table>
        <tr><td>Projet</td><td>{projet}</td></tr>
        <tr><td>Deadline</td><td class="urgent">{deadline_str}</td></tr>
        <tr><td>Priorite</td><td>{task.get_priority_display()}</td></tr>
        <tr><td>Statut</td><td>{task.get_status_display()}</td></tr>
      </table>
    </div>
    <p class="message" style="background:#f0f9ff;border-radius:8px;padding:12px 16px;border-left:4px solid #0ea5e9;">
      <strong>Conseil :</strong> {conseil}
    </p>
"""

    html_body = _html_wrap(header_color, header_icon, "", body_html)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[task.assigned_to.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] send_deadline_alert: {e}")
        return False
