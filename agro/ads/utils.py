# utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from .models import Ad, AdRating
from django.db.models import Avg


def send_ad_notification(ad, notification_type):
    """Envoyer des notifications par email pour les annonces"""
    
    if notification_type == 'approved':
        subject = f'Votre annonce "{ad.title}" a été approuvée'
        template = 'emails/ad_approved.html'
    elif notification_type == 'rejected':
        subject = f'Votre annonce "{ad.title}" a été rejetée'
        template = 'emails/ad_rejected.html'
    elif notification_type == 'expiring':
        subject = f'Votre annonce "{ad.title}" expire bientôt'
        template = 'emails/ad_expiring.html'
    else:
        return False
    
    try:
        html_message = render_to_string(template, {'ad': ad})
        send_mail(
            subject=subject,
            message='',
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ad.author.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return False


def get_expiring_ads(days=7):
    """Obtenir les annonces qui expirent dans X jours"""
    expiry_date = timezone.now() + timedelta(days=days)
    return Ad.objects.filter(
        status='approved',
        campaign_end__lte=expiry_date,
        campaign_end__gt=timezone.now()
    )


def update_expired_ads():
    """Mettre à jour le statut des annonces expirées"""
    expired_ads = Ad.objects.filter(
        status='approved',
        campaign_end__lt=timezone.now()
    )
    
    count = expired_ads.update(status='expired')
    return count


def get_ad_statistics(ad):
    """Obtenir les statistiques d'une annonce"""
    ratings = AdRating.objects.filter(ad=ad)
    
    return {
        'total_ratings': ratings.count(),
        'average_rating': ratings.aggregate(Avg('rating'))['rating__avg'] or 0,
        'views_count': ad.views_count,
        'days_remaining': (ad.campaign_end - timezone.now()).days if ad.campaign_end > timezone.now() else 0,
        'is_expired': ad.campaign_end < timezone.now(),
    }


def get_user_ad_statistics(user):
    """Obtenir les statistiques des annonces d'un utilisateur"""
    ads = Ad.objects.filter(author=user)
    
    return {
        'total_ads': ads.count(),
        'approved_ads': ads.filter(status='approved').count(),
        'pending_ads': ads.filter(status='pending').count(),
        'rejected_ads': ads.filter(status='rejected').count(),
        'expired_ads': ads.filter(status='expired').count(),
        'featured_ads': ads.filter(is_featured=True).count(),
        'total_views': sum(ad.views_count for ad in ads),
        'total_ratings': AdRating.objects.filter(ad__author=user).count(),
    }


def get_trending_ads(limit=10):
    """Obtenir les annonces tendances basées sur les vues et ratings récents"""
    from django.db.models import F, ExpressionWrapper, FloatField
    
    # Calculer un score basé sur les vues et l'âge de l'annonce
    ads = Ad.objects.filter(
        status='approved',
        campaign_end__gt=timezone.now()
    ).annotate(
        days_old=ExpressionWrapper(
            timezone.now() - F('created_at'),
            output_field=FloatField()
        )
    ).annotate(
        trend_score=ExpressionWrapper(
            F('views_count') / (F('days_old') + 1),
            output_field=FloatField()
        )
    ).order_by('-trend_score')[:limit]
    
    return ads


def search_ads_advanced(query_params):
    """Recherche avancée d'annonces avec filtres multiples"""
    from django.db.models import Q
    
    ads = Ad.objects.filter(status='approved', campaign_end__gt=timezone.now())
    
    # Recherche textuelle
    if query_params.get('search'):
        search_terms = query_params['search'].split()
        search_query = Q()
        for term in search_terms:
            search_query |= (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(location__icontains=term)
            )
        ads = ads.filter(search_query)
    
    # Filtres par catégorie
    if query_params.get('category'):
        ads = ads.filter(category_id=query_params['category'])
    
    # Filtres de prix
    if query_params.get('min_price'):
        ads = ads.filter(price__gte=query_params['min_price'])
    if query_params.get('max_price'):
        ads = ads.filter(price__lte=query_params['max_price'])
    
    # Filtre par localisation
    if query_params.get('location'):
        ads = ads.filter(location__icontains=query_params['location'])
    
    # Filtre par type d'auteur
    if query_params.get('author_type'):
        ads = ads.filter(author__user_type=query_params['author_type'])
    
    # Filtre annonces en vedette
    if query_params.get('is_featured'):
        ads = ads.filter(is_featured=True)
    
    # Tri
    sort_by = query_params.get('sort', 'newest')
    if sort_by == 'oldest':
        ads = ads.order_by('created_at')
    elif sort_by == 'price_low':
        ads = ads.order_by('price')
    elif sort_by == 'price_high':
        ads = ads.order_by('-price')
    elif sort_by == 'views':
        ads = ads.order_by('-views_count')
    else:  # newest (default)
        ads = ads.order_by('-created_at')
    
    return ads


# signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Ad, AdRating


@receiver(post_save, sender=Ad)
def ad_status_changed(sender, instance, created, **kwargs):
    """Signal déclenché quand le statut d'une annonce change"""
    if not created:  # Modification d'une annonce existante
        # Récupérer l'ancien statut depuis la base
        try:
            old_instance = Ad.objects.get(pk=instance.pk)
            if hasattr(old_instance, '_state') and old_instance._state.adding:
                return
                
            # Vérifier si le statut a changé
            previous_status = getattr(instance, '_previous_status', None)
            if previous_status and previous_status != instance.status:
                if instance.status == 'approved':
                    send_ad_notification(instance, 'approved')
                elif instance.status == 'rejected':
                    send_ad_notification(instance, 'rejected')
        except Ad.DoesNotExist:
            pass


@receiver(pre_save, sender=Ad)
def store_previous_status(sender, instance, **kwargs):
    """Stocker le statut précédent avant sauvegarde"""
    if instance.pk:
        try:
            old_instance = Ad.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Ad.DoesNotExist:
            pass


@receiver(post_save, sender=AdRating)
def rating_added(sender, instance, created, **kwargs):
    """Signal déclenché quand une note est ajoutée"""
    if created:
        # Optionnel: notifier l'auteur de l'annonce qu'il a reçu une note
        pass


# management/commands/update_expired_ads.py
# Commande Django pour mettre à jour les annonces expirées
from django.core.management.base import BaseCommand
from django.utils import timezone
from ...models import Ad


class Command(BaseCommand):
    help = 'Met à jour le statut des annonces expirées'

    def handle(self, *args, **options):
        expired_count = update_expired_ads()
        self.stdout.write(
            self.style.SUCCESS(
                f'{expired_count} annonce(s) marquée(s) comme expirée(s)'
            )
        )


# management/commands/send_expiry_notifications.py
# Commande pour envoyer les notifications d'expiration
from django.core.management.base import BaseCommand
from ...utils import get_expiring_ads, send_ad_notification


class Command(BaseCommand):
    help = 'Envoie des notifications pour les annonces qui expirent bientôt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Nombre de jours avant expiration'
        )

    def handle(self, *args, **options):
        days = options['days']
        expiring_ads = get_expiring_ads(days)
        
        sent_count = 0
        for ad in expiring_ads:
            if send_ad_notification(ad, 'expiring'):
                sent_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{sent_count} notification(s) d\'expiration envoyée(s)'
            )
        )


# admin.py - Configuration de l'admin Django
from django.contrib import admin
from .models import Category, Ad, AdImage, AdRating


class AdImageInline(admin.TabularInline):
    model = AdImage
    extra = 1
    max_num = 10


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    prepopulated_fields = {'name': ('name',)}


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'category', 'status', 'is_featured', 
        'views_count', 'created_at', 'campaign_end'
    ]
    list_filter = [
        'status', 'is_featured', 'category', 'author__user_type', 'created_at'
    ]
    search_fields = ['title', 'description', 'author__username']
    date_hierarchy = 'created_at'
    inlines = [AdImageInline]
    readonly_fields = ['views_count', 'created_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'description', 'category', 'author')
        }),
        ('Détails', {
            'fields': ('location', 'price')
        }),
        ('Campagne', {
            'fields': ('campaign_start', 'campaign_end', 'status', 'is_featured')
        }),
        ('Statistiques', {
            'fields': ('views_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')


@admin.register(AdRating)
class AdRatingAdmin(admin.ModelAdmin):
    list_display = ['ad', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['ad__title', 'user__username']
    date_hierarchy = 'created_at'