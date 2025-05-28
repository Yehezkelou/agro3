
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import Formation, FormationCategory, UserFormation, FormationReview


# Vues basées sur les fonctions
def formation_list(request):
    """Liste des formations avec filtrage et pagination"""
    formations = Formation.objects.filter(
        is_active=True, 
        status='PUBLISHED'
    ).select_related('category').prefetch_related('userformation_set')
    
    # Filtres
    category_slug = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search_query = request.GET.get('search')
    price_filter = request.GET.get('price')  # free, paid, all
    sort_by = request.GET.get('sort', 'newest')  # newest, popular, price_low, price_high
    
    # Application des filtres
    if category_slug:
        formations = formations.filter(category__slug=category_slug)
    
    if difficulty:
        formations = formations.filter(difficulty=difficulty)
    
    if search_query:
        formations = formations.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(meta_keywords__icontains=search_query)
        )
    
    if price_filter == 'free':
        formations = formations.filter(is_free=True)
    elif price_filter == 'paid':
        formations = formations.filter(is_free=False)
    
    # Tri
    if sort_by == 'newest':
        formations = formations.order_by('-published_at', '-created_at')
    elif sort_by == 'popular':
        formations = formations.annotate(
            enrollment_count=Count('userformation')
        ).order_by('-enrollment_count')
    elif sort_by == 'price_low':
        formations = formations.order_by('price')
    elif sort_by == 'price_high':
        formations = formations.order_by('-price')
    elif sort_by == 'rating':
        formations = formations.annotate(
            avg_rating=Avg('userformation__rating')
        ).order_by('-avg_rating')
    
    # Pagination
    paginator = Paginator(formations, 12)  # 12 formations par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Données pour les filtres
    categories = FormationCategory.objects.annotate(
    formation_count=Count('formation', filter=Q(formation__is_active=True))
)
    
    difficulty_choices = Formation.DIFFICULTY_LEVELS
    
    # Formations en vedette (sidebar ou header)
    featured_formations = Formation.objects.filter(
        is_active=True,
        status='PUBLISHED',
        is_featured=True
    )[:3]
    
    context = {
        'page_obj': page_obj,
        'formations': page_obj.object_list,
        'categories': categories,
        'difficulty_choices': difficulty_choices,
        'featured_formations': featured_formations,
        'current_category': category_slug,
        'current_difficulty': difficulty,
        'current_search': search_query,
        'current_price_filter': price_filter,
        'current_sort': sort_by,
        'total_formations': paginator.count,
    }
    
    return render(request, 'formations/list.html', context)


def formation_detail(request, slug):
    """Détail d'une formation"""
    formation = get_object_or_404(
        Formation.objects.select_related('category').prefetch_related(
            'userformation_set__user',
            'userformation_set__formationreview'
        ),
        slug=slug,
        is_active=True,
        status='PUBLISHED'
    )
    
    # Vérifier si l'utilisateur est inscrit
    user_enrollment = None
    is_enrolled = False
    can_access = False
    
    if request.user.is_authenticated:
        try:
            user_enrollment = UserFormation.objects.get(
                user=request.user,
                formation=formation
            )
            is_enrolled = True
            can_access = user_enrollment.can_access_content
        except UserFormation.DoesNotExist:
            pass
    
    # Statistiques de la formation
    total_enrolled = formation.enrolled_count
    completion_rate = formation.completion_rate
    
    # Avis et notes
    reviews = FormationReview.objects.filter(
        user_formation__formation=formation,
        is_approved=True
    ).select_related('user_formation__user').order_by('-created_at')[:5]
    
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    rating_breakdown = {}
    for i in range(1, 6):
        rating_breakdown[i] = reviews.filter(rating=i).count()
    
    # Formations similaires
    similar_formations = Formation.objects.filter(
        category=formation.category,
        is_active=True,
        status='PUBLISHED'
    ).exclude(pk=formation.pk)[:4]
    
    context = {
        'formation': formation,
        'user_enrollment': user_enrollment,
        'is_enrolled': is_enrolled,
        'can_access': can_access,
        'total_enrolled': total_enrolled,
        'completion_rate': completion_rate,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'rating_breakdown': rating_breakdown,
        'similar_formations': similar_formations,
        'is_full': formation.is_full,
        'discount_percentage': formation.discount_percentage,
    }
    
    return render(request, 'formations/detail.html', context)


def category_detail(request, slug):
    """Détail d'une catégorie avec ses formations"""
    category = get_object_or_404(FormationCategory, slug=slug, is_active=True)
    
    formations = Formation.objects.filter(
        category=category,
        is_active=True,
        status='PUBLISHED'
    ).select_related('category')
    
    # Pagination
    paginator = Paginator(formations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'formations': page_obj.object_list,
        'total_formations': paginator.count,
    }
    
    return render(request, 'formations/category_detail.html', context)


@login_required
@require_http_methods(["POST"])
def enroll_formation(request, slug):
    """Inscription à une formation"""
    formation = get_object_or_404(Formation, slug=slug, is_active=True)
    
    # Vérifier si l'utilisateur est déjà inscrit
    if UserFormation.objects.filter(user=request.user, formation=formation).exists():
        messages.warning(request, _("Vous êtes déjà inscrit à cette formation."))
        return redirect('formations:detail', slug=slug)
    
    # Vérifier si la formation est complète
    if formation.is_full:
        messages.error(request, _("Cette formation est complète."))
        return redirect('formations:detail', slug=slug)
    
    # Créer l'inscription
    enrollment = UserFormation.objects.create(
        user=request.user,
        formation=formation,
        amount_paid=formation.price,
        payment_status='COMPLETED' if formation.is_free else 'PENDING'
    )
    
    if formation.is_free:
        messages.success(request, _("Inscription réussie ! Vous pouvez maintenant accéder à la formation."))
    else:
        messages.info(request, _("Inscription en attente. Veuillez procéder au paiement."))
        # Rediriger vers la page de paiement
        return redirect('payments:process', enrollment_id=enrollment.id)
    
    return redirect('formations:detail', slug=slug)


@login_required
def my_formations(request):
    """Formations de l'utilisateur"""
    enrollments = UserFormation.objects.filter(
        user=request.user
    ).select_related('formation', 'formation__category').order_by('-date_enrolled')
    
    # Filtres
    status_filter = request.GET.get('status', 'all')  # all, completed, in_progress, pending
    
    if status_filter == 'completed':
        enrollments = enrollments.filter(completed=True)
    elif status_filter == 'in_progress':
        enrollments = enrollments.filter(
            payment_status='COMPLETED',
            completed=False
        )
    elif status_filter == 'pending':
        enrollments = enrollments.filter(payment_status='PENDING')
    
    # Pagination
    paginator = Paginator(enrollments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': enrollments.count(),
        'completed': enrollments.filter(completed=True).count(),
        'in_progress': enrollments.filter(
            payment_status='COMPLETED',
            completed=False
        ).count(),
        'pending': enrollments.filter(payment_status='PENDING').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'enrollments': page_obj.object_list,
        'current_status': status_filter,
        'stats': stats,
    }
    
    return render(request, 'formations/my_formations.html', context)


@login_required
def formation_content(request, slug):
    """Accès au contenu de la formation"""
    formation = get_object_or_404(Formation, slug=slug, is_active=True)
    
    try:
        enrollment = UserFormation.objects.get(
            user=request.user,
            formation=formation
        )
    except UserFormation.DoesNotExist:
        messages.error(request, _("Vous devez vous inscrire à cette formation."))
        return redirect('formations:detail', slug=slug)
    
    if not enrollment.can_access_content:
        messages.error(request, _("Accès refusé. Veuillez compléter votre paiement."))
        return redirect('formations:detail', slug=slug)
    
    context = {
        'formation': formation,
        'enrollment': enrollment,
    }
    
    return render(request, 'formations/content.html', context)


@login_required
@require_http_methods(["POST"])
def update_progress(request, slug):
    """Mise à jour de la progression (AJAX)"""
    formation = get_object_or_404(Formation, slug=slug)
    
    try:
        enrollment = UserFormation.objects.get(
            user=request.user,
            formation=formation
        )
    except UserFormation.DoesNotExist:
        return JsonResponse({'error': 'Inscription non trouvée'}, status=404)
    
    if not enrollment.can_access_content:
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    try:
        progress = int(request.POST.get('progress', 0))
        enrollment.update_progress(progress)
        
        return JsonResponse({
            'success': True,
            'progress': enrollment.progress_percentage,
            'completed': enrollment.completed
        })
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Progression invalide'}, status=400)


@login_required
@require_http_methods(["POST"])
def submit_review(request, slug):
    """Soumettre un avis sur une formation"""
    formation = get_object_or_404(Formation, slug=slug)
    
    try:
        enrollment = UserFormation.objects.get(
            user=request.user,
            formation=formation,
            payment_status='COMPLETED'
        )
    except UserFormation.DoesNotExist:
        messages.error(request, _("Vous devez avoir suivi cette formation pour laisser un avis."))
        return redirect('formations:detail', slug=slug)
    
    # Vérifier si un avis existe déjà
    if hasattr(enrollment, 'formationreview'):
        messages.warning(request, _("Vous avez déjà laissé un avis pour cette formation."))
        return redirect('formations:detail', slug=slug)
    
    rating = request.POST.get('rating')
    title = request.POST.get('title')
    content = request.POST.get('content')
    
    if not all([rating, title, content]):
        messages.error(request, _("Tous les champs sont requis."))
        return redirect('formations:detail', slug=slug)
    
    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, _("Note invalide."))
        return redirect('formations:detail', slug=slug)
    
    # Créer l'avis
    FormationReview.objects.create(
        user_formation=enrollment,
        rating=rating,
        title=title,
        content=content,
        is_verified=enrollment.completed
    )
    
    messages.success(request, _("Votre avis a été soumis avec succès."))
    return redirect('formations:detail', slug=slug)


# Vues basées sur les classes (alternatives)
class FormationListView(ListView):
    """Vue classe pour la liste des formations"""
    model = Formation
    template_name = 'formations/list.html'
    context_object_name = 'formations'
    paginate_by = 12
    
    def get_queryset(self):
        return Formation.objects.filter(
            is_active=True,
            status='PUBLISHED'
        ).select_related('category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = FormationCategory.objects.filter(is_active=True)
        context['difficulty_choices'] = Formation.DIFFICULTY_LEVELS
        return context


class FormationDetailView(DetailView):
    """Vue classe pour le détail d'une formation"""
    model = Formation
    template_name = 'formations/detail.html'
    context_object_name = 'formation'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Formation.objects.filter(
            is_active=True,
            status='PUBLISHED'
        ).select_related('category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formation = self.object
        
        # Inscription de l'utilisateur
        if self.request.user.is_authenticated:
            try:
                context['user_enrollment'] = UserFormation.objects.get(
                    user=self.request.user,
                    formation=formation
                )
                context['is_enrolled'] = True
            except UserFormation.DoesNotExist:
                context['is_enrolled'] = False
        
        # Formations similaires
        context['similar_formations'] = Formation.objects.filter(
            category=formation.category,
            is_active=True,
            status='PUBLISHED'
        ).exclude(pk=formation.pk)[:4]
        
        return context


# Vues API pour AJAX
def search_formations_ajax(request):
    """Recherche AJAX des formations"""
    query = request.GET.get('q', '')
    if len(query) < 3:
        return JsonResponse({'results': []})
    
    formations = Formation.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        is_active=True,
        status='PUBLISHED'
    )[:10]
    
    results = [{
        'id': f.id,
        'title': f.title,
        'slug': f.slug,
        'price': str(f.price),
        'category': f.category.name if f.category else '',
        'thumbnail': f.thumbnail.url if f.thumbnail else '',
    } for f in formations]
    
    return JsonResponse({'results': results})