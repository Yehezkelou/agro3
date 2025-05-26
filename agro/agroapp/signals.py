# core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from ads.models import Ad, Category

@receiver(post_save, sender=Ad)
@receiver(post_delete, sender=Ad)
def clear_stats_cache(sender, **kwargs):
    """Efface le cache des statistiques quand une annonce change"""
    cache.delete('platform_stats')
    cache.delete('featured_ads')

@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def clear_category_cache(sender, **kwargs):
    """Efface le cache des catégories"""
    cache.delete('global_categories')