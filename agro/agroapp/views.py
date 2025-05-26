# core/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ads.models import Ad, Category
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

def home(request):
    """
    Vue d'accueil avec statistiques en temps réel et annonces vedettes
    """
    # Annonces en vedette (maximum 6)
    featured_ads = Ad.objects.filter(
        status='approved', 
        is_featured=True,
        expires_at__gt=timezone.now()
    ).select_related('category', 'author').prefetch_related('images')[:6]
    
    # Annonces urgentes (maximum 4)
    urgent_ads = Ad.objects.filter(
        status='approved', 
        is_urgent=True,
        expires_at__gt=timezone.now()
    ).select_related('category', 'author').prefetch_related('images')[:4]
    
    # Annonces récentes (maximum 8)
    recent_ads = Ad.objects.filter(
        status='approved',
        expires_at__gt=timezone.now()
    ).select_related('category', 'author').prefetch_related('images').order_by('-created_at')[:8]
    
    # Toutes les catégories avec comptage d'annonces
    categories = Category.objects.annotate(
        ad_count=Count('ad', filter=Q(ad__status='approved', ad__expires_at__gt=timezone.now()))
    ).order_by('name')
    
    # Statistiques globales en temps réel
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    
    stats = {
        'total_ads': Ad.objects.filter(status='approved', expires_at__gt=now).count(),
        'total_categories': categories.count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'new_ads_this_month': Ad.objects.filter(
            status='approved', 
            created_at__gte=thirty_days_ago,
            expires_at__gt=now
        ).count(),
        'featured_count': featured_ads.count(),
        'urgent_count': urgent_ads.count(),
    }
    
    # Top catégories (les plus populaires)
    top_categories = categories.filter(ad_count__gt=0).order_by('-ad_count')[:5]
    
    context = {
        'featured_ads': featured_ads,
        'urgent_ads': urgent_ads,
        'recent_ads': recent_ads,
        'categories': categories,
        'top_categories': top_categories,
        'stats': stats,
        'page_title': 'Accueil - Plateforme Agricole Professionnelle'
    }
    
    return render(request, 'core/home.html', context)

def search(request):
    """
    Vue de recherche avancée avec filtres multiples
    """
    # Paramètres de recherche
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    location = request.GET.get('location', '').strip()
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    sort_by = request.GET.get('sort', '-created_at')
    is_urgent = request.GET.get('urgent')
    is_featured = request.GET.get('featured')
    
    # Base queryset
    ads = Ad.objects.filter(
        status='approved',
        expires_at__gt=timezone.now()
    ).select_related('category', 'author').prefetch_related('images')
    
    # Filtres de recherche
    if query:
        ads = ads.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    if category_id and category_id.isdigit():
        ads = ads.filter(category_id=category_id)
    
    if location:
        ads = ads.filter(location__icontains=location)
    
    if price_min and price_min.replace('.', '').isdigit():
        ads = ads.filter(price__gte=float(price_min))
    
    if price_max and price_max.replace('.', '').isdigit():
        ads = ads.filter(price__lte=float(price_max))
    
    if is_urgent == 'on':
        ads = ads.filter(is_urgent=True)
    
    if is_featured == 'on':
        ads = ads.filter(is_featured=True)
    
    # Tri des résultats
    sort_options = {
        '-created_at': 'Plus récentes',
        'created_at': 'Plus anciennes',
        'price': 'Prix croissant',
        '-price': 'Prix décroissant',
        'title': 'Titre A-Z',
        '-views_count': 'Plus vues',
    }
    
    if sort_by in sort_options:
        if sort_by in ['price', '-price']:
            ads = ads.filter(price__isnull=False).order_by(sort_by)
        else:
            ads = ads.order_by(sort_by)
    else:
        ads = ads.order_by('-is_featured', '-is_urgent', '-created_at')
    
    # Pagination
    paginator = Paginator(ads, 12)
    page_number = request.GET.get('page', 1)
    ads_page = paginator.get_page(page_number)
    
    # Toutes les catégories pour le filtre
    categories = Category.objects.annotate(
        ad_count=Count('ad', filter=Q(ad__status='approved', ad__expires_at__gt=timezone.now()))
    ).order_by('name')
    
    # Statistiques de recherche
    total_results = ads.count()
    
    context = {
        'ads': ads_page,
        'categories': categories,
        'search_query': query,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
        'selected_location': location,
        'price_min': price_min,
        'price_max': price_max,
        'sort_by': sort_by,
        'sort_options': sort_options,
        'is_urgent': is_urgent,
        'is_featured': is_featured,
        'total_results': total_results,
        'page_title': f'Recherche: {query}' if query else 'Recherche d\'annonces'
    }
    
    return render(request, 'ads/ad_list.html', context)

def category_list(request):
    """
    Vue listant toutes les catégories avec statistiques
    """
    categories = Category.objects.annotate(
        ad_count=Count('ad', filter=Q(ad__status='approved', ad__expires_at__gt=timezone.now())),
        featured_count=Count('ad', filter=Q(
            ad__status='approved', 
            ad__is_featured=True,
            ad__expires_at__gt=timezone.now()
        ))
    ).order_by('name')
    
    context = {
        'categories': categories,
        'page_title': 'Toutes les catégories'
    }
    
    return render(request, 'core/categories.html', context)

def category_detail(request, category_id):
    """
    Vue détaillée d'une catégorie avec ses annonces
    """
    category = get_object_or_404(Category, id=category_id)
    
    # Annonces de cette catégorie
    ads = Ad.objects.filter(
        category=category,
        status='approved',
        expires_at__gt=timezone.now()
    ).select_related('author').prefetch_related('images').order_by('-is_featured', '-is_urgent', '-created_at')
    
    # Pagination
    paginator = Paginator(ads, 12)
    page_number = request.GET.get('page', 1)
    ads_page = paginator.get_page(page_number)
    
    # Statistiques de la catégorie
    stats = {
        'total_ads': ads.count(),
        'featured_ads': ads.filter(is_featured=True).count(),
        'urgent_ads': ads.filter(is_urgent=True).count(),
        'avg_price': ads.filter(price__isnull=False).aggregate(
            avg_price=models.Avg('price')
        )['avg_price'] or 0
    }
    
    context = {
        'category': category,
        'ads': ads_page,
        'stats': stats,
        'page_title': f'Catégorie: {category.name}'
    }
    
    return render(request, 'core/category_detail.html', context)

def statistics(request):
    """
    Vue des statistiques globales de la plateforme
    """
    now = timezone.now()
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    last_year = now - timedelta(days=365)
    
    # Statistiques générales
    total_ads = Ad.objects.filter(status='approved').count()
    active_ads = Ad.objects.filter(status='approved', expires_at__gt=now).count()
    expired_ads = Ad.objects.filter(status='approved', expires_at__lte=now).count()
    
    # Statistiques temporelles
    ads_this_week = Ad.objects.filter(created_at__gte=last_week).count()
    ads_this_month = Ad.objects.filter(created_at__gte=last_month).count()
    ads_this_year = Ad.objects.filter(created_at__gte=last_year).count()
    
    # Top catégories
    top_categories = Category.objects.annotate(
        ad_count=Count('ad', filter=Q(ad__status='approved'))
    ).order_by('-ad_count')[:10]
    
    # Utilisateurs les plus actifs
    top_users = User.objects.annotate(
        ad_count=Count('ad', filter=Q(ad__status='approved'))
    ).filter(ad_count__gt=0).order_by('-ad_count')[:10]
    
    # Évolution mensuelle (12 derniers mois)
    monthly_stats = []
    for i in range(12):
        month_start = now.replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        month_ads = Ad.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        monthly_stats.append({
            'month': month_start.strftime('%m/%Y'),
            'ads_count': month_ads
        })
    
    monthly_stats.reverse()
    
    context = {
        'total_ads': total_ads,
        'active_ads': active_ads,
        'expired_ads': expired_ads,
        'ads_this_week': ads_this_week,
        'ads_this_month': ads_this_month,
        'ads_this_year': ads_this_year,
        'top_categories': top_categories,
        'top_users': top_users,
        'monthly_stats': monthly_stats,
        'page_title': 'Statistiques de la plateforme'
    }
    
    return render(request, 'core/statistics.html', context)

@require_http_methods(["GET"])
def search_suggestions(request):
    """
    API pour l'autocomplétion de recherche (AJAX)
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Suggestions basées sur les titres d'annonces
    title_suggestions = Ad.objects.filter(
        title__icontains=query,
        status='approved',
        expires_at__gt=timezone.now()
    ).values_list('title', flat=True).distinct()[:5]
    
    # Suggestions basées sur les catégories
    category_suggestions = Category.objects.filter(
        name__icontains=query
    ).values_list('name', flat=True)[:3]
    
    # Suggestions basées sur les localisations
    location_suggestions = Ad.objects.filter(
        location__icontains=query,
        status='approved',
        expires_at__gt=timezone.now()
    ).values_list('location', flat=True).distinct()[:3]
    
    suggestions = {
        'titles': list(title_suggestions),
        'categories': list(category_suggestions),
        'locations': list(location_suggestions)
    }
    
    return JsonResponse({'suggestions': suggestions})

def about(request):
    """
    Page À propos avec informations sur la plateforme
    """
    # Quelques statistiques pour la page about
    stats = {
        'total_ads': Ad.objects.filter(status='approved').count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'total_categories': Category.objects.count(),
        'platform_age': timezone.now().year - 2024  # Supposons que la plateforme a commencé en 2024
    }
    
    context = {
        'stats': stats,
        'page_title': 'À propos de nous'
    }
    
    return render(request, 'core/about.html', context)

def contact(request):
    """
    Page de contact
    """
    if request.method == 'POST':
        # Ici vous pourrez ajouter la logique d'envoi d'email
        # Pour l'instant, on simule juste un message de succès
        from django.contrib import messages
        messages.success(request, 'Votre message a été envoyé avec succès!')
        return redirect('core:contact')
    
    context = {
        'page_title': 'Nous contacter'
    }
    
    return render(request, 'core/contact.html', context)