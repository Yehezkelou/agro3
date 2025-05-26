from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import UserProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crée un profil utilisateur automatiquement lors de la création d'un User.
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """
    Sauvegarde le profil utilisateur à chaque mise à jour du User.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
