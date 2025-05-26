from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_welcome_email(user):
    subject = 'Bienvenue sur AgriPub!'
    html_message = render_to_string('users/emails/welcome.html', {
        'user': user,
        'site_name': settings.SITE_NAME
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email
    
    send_mail(subject, plain_message, from_email, [to], html_message=html_message)

def send_password_reset_email(user, reset_link):
    subject = 'Réinitialisation de votre mot de passe'
    html_message = render_to_string('users/emails/password_reset.html', {
        'user': user,
        'reset_link': reset_link,
        'site_name': settings.SITE_NAME
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email
    
    send_mail(subject, plain_message, from_email, [to], html_message=html_message)