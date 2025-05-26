from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Advertisement, Favorite


class AdvertisementService:
    @staticmethod
    def get_published_ads(page=1, per_page=10, filters=None):
        """Récupère les annonces publiées avec filtres et pagination"""
        queryset = Advertisement.objects.filter(
            status='published'
        ).select_related('author', 'category').prefetch_related('images')
        
        if filters:
            if filters.get('category'):
                queryset = queryset.filter(category=filters['category'])
            if filters.get('min_price'):
                queryset = queryset.filter(price__gte=filters['min_price'])
            if filters.get('max_price'):
                queryset = queryset.filter(price__lte=filters['max_price'])
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(author__username__icontains=search_term)
                )
            if filters.get('premium_only'):
                queryset = queryset.filter(is_premium=True)
        
        # Correction: utiliser created_at au lieu de publish
        paginator = Paginator(queryset.order_by('-is_premium', '-created_at'), per_page)
        return paginator.get_page(page)

    @staticmethod
    def get_user_ads(user, page=1, per_page=10, status_filter=None):
        """Récupère les annonces d'un utilisateur avec pagination"""
        queryset = Advertisement.objects.filter(
            author=user
        ).select_related('category').prefetch_related('images')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        paginator = Paginator(queryset.order_by('-created_at'), per_page)
        return paginator.get_page(page)

    @staticmethod
    def get_favorite_ads(user, page=1, per_page=10):
        """Récupère les annonces favorites d'un utilisateur"""
        # Correction: utiliser la relation correcte via le modèle Favorite
        queryset = Advertisement.objects.filter(
            favorite__user=user
        ).select_related('author', 'category').prefetch_related('images')
        
        paginator = Paginator(queryset.order_by('-created_at'), per_page)
        return paginator.get_page(page)

    @staticmethod
    def get_category_ads(category, page=1, per_page=10):
        """Récupère les annonces d'une catégorie spécifique"""
        queryset = Advertisement.objects.filter(
            category=category,
            status='published'
        ).select_related('author', 'category').prefetch_related('images')
        
        paginator = Paginator(queryset.order_by('-is_premium', '-created_at'), per_page)
        return paginator.get_page(page)

    @staticmethod
    def get_premium_ads(limit=5):
        """Récupère les annonces premium pour affichage spécial"""
        return Advertisement.objects.filter(
            status='published',
            is_premium=True
        ).select_related('author', 'category').prefetch_related('images')[:limit]

    @staticmethod
    def get_latest_ads(limit=10):
        """Récupère les dernières annonces publiées"""
        return Advertisement.objects.filter(
            status='published'
        ).select_related('author', 'category').prefetch_related('images').order_by('-created_at')[:limit]

    @staticmethod
    def search_ads(query, page=1, per_page=10):
        """Recherche avancée dans les annonces"""
        if not query:
            return Advertisement.objects.none()
        
        queryset = Advertisement.objects.filter(
            status='published'
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(author__username__icontains=query)
        ).select_related('author', 'category').prefetch_related('images')
        
        paginator = Paginator(queryset.order_by('-is_premium', '-created_at'), per_page)
        return paginator.get_page(page)

    @staticmethod
    def get_stats():
        """Récupère des statistiques sur les annonces"""
        total_ads = Advertisement.objects.count()
        published_ads = Advertisement.objects.filter(status='published').count()
        premium_ads = Advertisement.objects.filter(is_premium=True).count()
        draft_ads = Advertisement.objects.filter(status='draft').count()
        
        return {
            'total': total_ads,
            'published': published_ads,
            'premium': premium_ads,
            'draft': draft_ads,
        }

    @staticmethod
    def get_user_stats(user):
        """Récupère les statistiques d'un utilisateur"""
        user_ads = Advertisement.objects.filter(author=user)
        favorites_count = Favorite.objects.filter(user=user).count()
        
        return {
            'total_ads': user_ads.count(),
            'published_ads': user_ads.filter(status='published').count(),
            'draft_ads': user_ads.filter(status='draft').count(),
            'premium_ads': user_ads.filter(is_premium=True).count(),
            'favorites_count': favorites_count,
        }

    @staticmethod
    def is_favorited_by_user(advertisement, user):
        """Vérifie si une annonce est dans les favoris d'un utilisateur"""
        if not user.is_authenticated:
            return False
        return Favorite.objects.filter(
            user=user,
            advertisement=advertisement
        ).exists()

    @staticmethod
    def toggle_favorite(advertisement, user):
        """Ajoute ou retire une annonce des favoris"""
        if not user.is_authenticated:
            return False, "Utilisateur non connecté"
        
        favorite, created = Favorite.objects.get_or_create(
            user=user,
            advertisement=advertisement
        )
        
        if not created:
            favorite.delete()
            return False, "Retiré des favoris"
        return True, "Ajouté aux favoris"

    @staticmethod
    def get_related_ads(advertisement, limit=4):
        """Récupère des annonces similaires"""
        return Advertisement.objects.filter(
            category=advertisement.category,
            status='published'
        ).exclude(
            id=advertisement.id
        ).select_related('author', 'category').prefetch_related('images')[:limit]


# Classe alternative pour une gestion plus avancée
class AdvancedAdvertisementService(AdvertisementService):
    """Service étendu avec des fonctionnalités avancées"""
    
    @staticmethod
    def get_ads_with_stats(page=1, per_page=10, filters=None):
        """Récupère les annonces avec des statistiques (nombre de favoris, etc.)"""
        queryset = Advertisement.objects.filter(
            status='published'
        ).select_related('author', 'category').prefetch_related('images').annotate(
            favorites_count=Count('favorite')
        )
        
        if filters:
            # Appliquer les mêmes filtres que la classe parent
            if filters.get('category'):
                queryset = queryset.filter(category=filters['category'])
            if filters.get('min_price'):
                queryset = queryset.filter(price__gte=filters['min_price'])
            if filters.get('max_price'):
                queryset = queryset.filter(price__lte=filters['max_price'])
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(description__icontains=search_term)
                )
            if filters.get('premium_only'):
                queryset = queryset.filter(is_premium=True)
        
        paginator = Paginator(queryset.order_by('-is_premium', '-created_at'), per_page)
        return paginator.get_page(page)

    @staticmethod
    def get_popular_ads(limit=10):
        """Récupère les annonces les plus populaires (basé sur les favoris)"""
        return Advertisement.objects.filter(
            status='published'
        ).select_related('author', 'category').prefetch_related('images').annotate(
            favorites_count=Count('favorite')
        ).order_by('-favorites_count')[:limit]