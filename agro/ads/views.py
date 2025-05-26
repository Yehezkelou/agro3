from django.shortcuts import render

# Create your views here.
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from .models import Ad, Category, AdImage, AdRating, CustomUser
from .forms import (
    AdForm, AdImageFormSet, AdRatingForm, AdSearchForm, 
    CategoryForm, AdStatusForm, BulkAdActionForm, ContactAdvertiserForm
)


# ===== VUES POUR LES CATÉGORIES =====

class CategoryListView(ListView):
    """Liste des catégories"""
    model = Category
    template_name = 'ads/category_list.html'
    context_object_name = 'categories'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter le count d'annonces par catégorie
        for category in context['categories']:
            category.ads_count = Ad.objects.filter(
                category=category, 
                status='approved'
            ).count()
        return context


@staff_member_required
def create_category(request):
    """Créer une nouvelle catégorie (admin seulement)"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie créée avec succès!')
            return redirect('ads:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'ads/category_form.html', {'form': form})


# ===== VUES POUR LES ANNONCES =====

class AdListView(ListView):
    """Liste des annonces avec recherche et filtres"""
    model = Ad
    template_name = 'ads/ad_list.html'
    context_object_name = 'ads'
    paginate_by = 12

    def get_queryset(self):
        queryset = Ad.objects.filter(
            status='approved',
            campaign_end__gt=timezone.now()
        ).select_related('category', 'author').prefetch_related('images')
        
        # Appliquer les filtres de recherche
        form = AdSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | 
                    Q(description__icontains=search)
                )
            
            category = form.cleaned_data.get('category')
            if category:
                queryset = queryset.filter(category=category)
            
            location = form.cleaned_data.get('location')
            if location:
                queryset = queryset.filter(location__icontains=location)
            
            min_price = form.cleaned_data.get('min_price')
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            
            max_price = form.cleaned_data.get('max_price')
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            
            author_type = form.cleaned_data.get('author_type')
            if author_type:
                queryset = queryset.filter(author__user_type=author_type)
            
            is_featured = form.cleaned_data.get('is_featured')
            if is_featured:
                queryset = queryset.filter(is_featured=True)
        
        # Trier par featured puis par date
        return queryset.order_by('-is_featured', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AdSearchForm(self.request.GET)
        context['featured_ads'] = Ad.objects.filter(
            status='approved',
            is_featured=True,
            campaign_end__gt=timezone.now()
        )[:6]
        return context


class AdDetailView(DetailView):
    """Détail d'une annonce"""
    model = Ad
    template_name = 'ads/ad_detail.html'
    context_object_name = 'ad'

    def get_queryset(self):
        return Ad.objects.select_related('category', 'author').prefetch_related(
            'images', 'adrating_set__user'
        )

    def get_object(self):
        obj = super().get_object()
        # Vérifier que l'annonce est visible
        if obj.status != 'approved' and obj.author != self.request.user:
            if not (self.request.user.is_authenticated and self.request.user.is_staff):
                raise Http404("Annonce non trouvée")
        
        # Incrémenter le compteur de vues
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formulaire de notation
        if self.request.user.is_authenticated and self.request.user != self.object.author:
            context['rating_form'] = AdRatingForm(
                user=self.request.user, 
                ad=self.object
            )
        
        # Formulaire de contact
        if self.request.user.is_authenticated:
            context['contact_form'] = ContactAdvertiserForm(
                user=self.request.user,
                ad=self.object
            )
        
        # Statistiques des ratings
        ratings = self.object.adrating_set.all()
        context['ratings'] = ratings
        context['average_rating'] = ratings.aggregate(Avg('rating'))['rating__avg']
        context['ratings_count'] = ratings.count()
        
        # Annonces similaires
        context['similar_ads'] = Ad.objects.filter(
            category=self.object.category,
            status='approved',
            campaign_end__gt=timezone.now()
        ).exclude(id=self.object.id)[:4]
        
        return context


@login_required
def create_ad(request):
    """Créer une nouvelle annonce"""
    if request.method == 'POST':
        form = AdForm(request.POST, user=request.user)
        formset = AdImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            ad = form.save()
            formset.instance = ad
            formset.save()
            
            messages.success(request, 'Annonce créée avec succès! Elle sera examinée avant publication.')
            return redirect('ad_detail', pk=ad.pk)
    else:
        form = AdForm(user=request.user)
        formset = AdImageFormSet()
    
    return render(request, 'ads/ad_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Créer une annonce'
    })


@login_required
def update_ad(request, pk):
    """Modifier une annonce"""
    ad = get_object_or_404(Ad, pk=pk)
    
    # Vérifier les permissions
    if ad.author != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'avez pas les permissions pour modifier cette annonce.")
        return redirect('ad_detail', pk=ad.pk)
    
    if request.method == 'POST':
        form = AdForm(request.POST, instance=ad, user=request.user)
        formset = AdImageFormSet(request.POST, request.FILES, instance=ad)
        
        if form.is_valid() and formset.is_valid():
            ad = form.save()
            formset.save()
            
            messages.success(request, 'Annonce mise à jour avec succès!')
            return redirect('ad_detail', pk=ad.pk)
    else:
        form = AdForm(instance=ad, user=request.user)
        formset = AdImageFormSet(instance=ad)
    
    return render(request, 'ads/ad_form.html', {
        'form': form,
        'formset': formset,
        'ad': ad,
        'title': 'Modifier l\'annonce'
    })


@login_required
def delete_ad(request, pk):
    """Supprimer une annonce"""
    ad = get_object_or_404(Ad, pk=pk)
    
    # Vérifier les permissions
    if ad.author != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'avez pas les permissions pour supprimer cette annonce.")
        return redirect('ads:ad_detail', pk=ad.pk)
    
    if request.method == 'POST':
        ad.delete()
        messages.success(request, 'Annonce supprimée avec succès!')
        return redirect('ads:my_ads')
    
    return render(request, 'ads/ad_confirm_delete.html', {'ad': ad})


@login_required
def my_ads(request):
    """Mes annonces"""
    ads = Ad.objects.filter(author=request.user).order_by('-created_at')
    
    # Filtrer par statut si demandé
    status_filter = request.GET.get('status')
    if status_filter:
        ads = ads.filter(status=status_filter)
    
    paginator = Paginator(ads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': ads.count(),
        'approved': ads.filter(status='approved').count(),
        'pending': ads.filter(status='pending').count(),
        'rejected': ads.filter(status='rejected').count(),
        'expired': ads.filter(status='expired').count(),
    }
    
    return render(request, 'ads/my_ads.html', {
        'page_obj': page_obj,
        'stats': stats,
        'current_status': status_filter
    })


# ===== VUES POUR LES RATINGS =====

@login_required
def add_rating(request, ad_pk):
    """Ajouter une note à une annonce"""
    ad = get_object_or_404(Ad, pk=ad_pk)
    
    if request.method == 'POST':
        form = AdRatingForm(request.POST, user=request.user, ad=ad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre note a été ajoutée avec succès!')
        else:
            messages.error(request, 'Erreur lors de l\'ajout de la note.')
    
    return redirect('ads:ad_detail', pk=ad_pk)


@login_required
def delete_rating(request, rating_pk):
    """Supprimer une note"""
    rating = get_object_or_404(AdRating, pk=rating_pk)
    
    if rating.user != request.user and not request.user.is_staff:
        messages.error(request, "Vous ne pouvez pas supprimer cette note.")
        return redirect('ads:ad_detail', pk=rating.ad.pk)
    
    if request.method == 'POST':
        ad_pk = rating.ad.pk
        rating.delete()
        messages.success(request, 'Note supprimée avec succès!')
        return redirect('ads:ad_detail', pk=ad_pk)
    
    return render(request, 'ads/rating_confirm_delete.html', {'rating': rating})


# ===== VUES ADMIN =====

@staff_member_required
def admin_ads(request):
    """Gestion des annonces (admin)"""
    ads = Ad.objects.select_related('category', 'author').order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status')
    if status_filter:
        ads = ads.filter(status=status_filter)
    
    search = request.GET.get('search')
    if search:
        ads = ads.filter(
            Q(title__icontains=search) | 
            Q(author__username__icontains=search)
        )
    
    paginator = Paginator(ads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'ads/admin_ads.html', {
        'page_obj': page_obj,
        'current_status': status_filter,
        'search_query': search
    })


@staff_member_required
def update_ad_status(request, pk):
    """Modifier le statut d'une annonce (admin)"""
    ad = get_object_or_404(Ad, pk=pk)
    
    if request.method == 'POST':
        form = AdStatusForm(request.POST, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, f'Statut de l\'annonce "{ad.title}" mis à jour!')
            return redirect('ads:admin_ads')
    else:
        form = AdStatusForm(instance=ad)
    
    return render(request, 'ads/ad_status_form.html', {
        'form': form,
        'ad': ad
    })


@staff_member_required
def bulk_ad_actions(request):
    """Actions en lot sur les annonces (admin)"""
    if request.method == 'POST':
        form = BulkAdActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            ad_ids = form.cleaned_data['selected_ads']
            
            ads = Ad.objects.filter(id__in=ad_ids)
            count = ads.count()
            
            if action == 'approve':
                ads.update(status='approved')
                messages.success(request, f'{count} annonce(s) approuvée(s).')
            elif action == 'reject':
                ads.update(status='rejected')
                messages.success(request, f'{count} annonce(s) rejetée(s).')
            elif action == 'feature':
                ads.update(is_featured=True)
                messages.success(request, f'{count} annonce(s) mise(s) en vedette.')
            elif action == 'unfeature':
                ads.update(is_featured=False)
                messages.success(request, f'{count} annonce(s) retirée(s) de la vedette.')
            elif action == 'delete':
                ads.delete()
                messages.success(request, f'{count} annonce(s) supprimée(s).')
    
    return redirect('ads:admin_ads')


# ===== VUES AJAX =====

def get_category_ads(request, category_id):
    """Obtenir les annonces d'une catégorie (AJAX)"""
    ads = Ad.objects.filter(
        category_id=category_id,
        status='approved',
        campaign_end__gt=timezone.now()
    ).values('id', 'title', 'location', 'price', 'created_at')[:10]
    
    return JsonResponse({'ads': list(ads)})


@login_required
def contact_advertiser(request, ad_pk):
    """Contacter l'auteur d'une annonce"""
    ad = get_object_or_404(Ad, pk=ad_pk)
    
    if request.method == 'POST':
        form = ContactAdvertiserForm(
            request.POST, 
            user=request.user, 
            ad=ad
        )
        if form.is_valid():
            # Envoyer l'email
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            phone = form.cleaned_data.get('phone', '')
            
            full_message = f"""
            Message de: {request.user.get_full_name() or request.user.username}
            Email: {request.user.email}
            {f'Téléphone: {phone}' if phone else ''}
            
            Concernant l'annonce: {ad.title}
            
            Message:
            {message}
            """
            
            try:
                send_mail(
                    subject=f"[Annonce] {subject}",
                    message=full_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ad.author.email],
                    fail_silently=False,
                )
                messages.success(request, 'Votre message a été envoyé avec succès!')
            except Exception as e:
                messages.error(request, 'Erreur lors de l\'envoi du message.')
        
        return redirect('ads:ad_detail', pk=ad_pk)
    
    return redirect('ads:ad_detail', pk=ad_pk)