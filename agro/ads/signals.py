from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Ad
from .utils import send_ad_notification


@receiver(pre_save, sender=Ad)
def store_previous_status(sender, instance, **kwargs):
    """Stocker le statut précédent avant sauvegarde"""
    if instance.pk:
        try:
            old_instance = Ad.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Ad.DoesNotExist:
            pass


@receiver(post_save, sender=Ad)
def handle_status_change(sender, instance, created, **kwargs):
    """Gérer le changement de statut d'une annonce"""
    if not created and hasattr(instance, '_previous_status'):
        if instance._previous_status != instance.status:
            if instance.status == 'approved':
                send_ad_notification(instance, 'approved')
            elif instance.status == 'rejected':
                send_ad_notification(instance, 'rejected')