from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.views import View
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Advertisement, Category, Favorite, AdvertisementImage
from .forms import AdvertisementForm, AdvertisementImageForm, AdvertisementFilterForm
from django.db.models import Count
from user.models import User
def home_view(request):
    
    
    context = {
        'total_ads': Advertisement.objects.filter(status='published').count(),
        'total_users': User.objects.count(),
        'total_categories': Category.objects.count(),
        'popular_categories': Category.objects.annotate(
            ad_count=Count('advertisements')
        ).order_by('-ad_count')[:6],
        'recent_ads': Advertisement.objects.filter(
            status='published'
        ).order_by('-created_at')[:8],
        'premium_ads': Advertisement.objects.filter(
            status='published', 
            is_premium=True
        ).order_by('-created_at')[:4],
    }
    return render(request, 'publicites/home.html', context)

class AdvertisementListView(ListView):
    model = Advertisement
    template_name = 'publicites/list.html'
    context_object_name = 'ads'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(status='published')
        
        # Filtrage
        form = AdvertisementFilterForm(self.request.GET)
        if form.is_valid():
            category = form.cleaned_data.get('category')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')
            search = form.cleaned_data.get('search')
            premium_only = form.cleaned_data.get('premium_only')
            
            if category:
                queryset = queryset.filter(category=category)
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | 
                    Q(description__icontains=search)
                )
            if premium_only:
                queryset = queryset.filter(is_premium=True)
        
        return queryset.order_by('-is_premium', '-created_at')  # Changé de publish à created_at
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AdvertisementFilterForm(self.request.GET)
        return context


class AdvertisementDetailView(DetailView):
    model = Advertisement
    template_name = 'publicites/detail.html'
    context_object_name = 'ad'
    
    def get_queryset(self):
        return super().get_queryset().select_related('author', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user,
                advertisement=self.object
            ).exists()
        return context


class AdvertisementCreateView(LoginRequiredMixin, CreateView):
    model = Advertisement
    form_class = AdvertisementForm
    template_name = 'publicites/create.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Annonce créée avec succès!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('publicites:detail', kwargs={'pk': self.object.pk})


class AdvertisementEditView(LoginRequiredMixin, UpdateView):
    model = Advertisement
    form_class = AdvertisementForm
    template_name = 'publicites/edit.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Annonce mise à jour avec succès!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('publicites:detail', kwargs={'pk': self.object.pk})


class AdvertisementDeleteView(LoginRequiredMixin, DeleteView):
    model = Advertisement
    template_name = 'publicites/delete.html'
    success_url = reverse_lazy('publicites:list')
    
    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Annonce supprimée avec succès!')
        return super().delete(request, *args, **kwargs)


class AdvertisementImageView(LoginRequiredMixin, View):
    def get(self, request, pk):
        ad = get_object_or_404(Advertisement, pk=pk, author=request.user)
        form = AdvertisementImageForm()
        images = ad.images.all()
        return render(request, 'publicites/image.html', {
            'form': form, 
            'ad': ad, 
            'images': images
        })

    def post(self, request, pk):
        ad = get_object_or_404(Advertisement, pk=pk, author=request.user)
        form = AdvertisementImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.advertisement = ad
            image.save()
            messages.success(request, "Image ajoutée avec succès.")
            return redirect('publicites:images', pk=pk)
        
        images = ad.images.all()
        return render(request, 'publicites/image.html', {
            'form': form, 
            'ad': ad, 
            'images': images
        })


@login_required
def advertisement_image_delete(request, pk, image_pk):
    """Vue pour supprimer une image spécifique"""
    ad = get_object_or_404(Advertisement, pk=pk, author=request.user)
    image = get_object_or_404(AdvertisementImage, pk=image_pk, advertisement=ad)
    
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image supprimée avec succès!')
        return redirect('publicites:images', pk=pk)
    
    return render(request, 'publicites/image_delete.html', {
        'ad': ad, 
        'image': image
    })


@login_required
def toggle_favorite(request, pk):
    ad = get_object_or_404(Advertisement, pk=pk)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        advertisement=ad
    )
    
    if not created:
        favorite.delete()
        messages.success(request, 'Annonce retirée de vos favoris.')
    else:
        messages.success(request, 'Annonce ajoutée à vos favoris!')
    
    return redirect('publicites:detail', pk=pk)


@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('advertisement')
    return render(request, 'publicites/favorites.html', {'favorites': favorites})


# API Views (si vous utilisez Django REST Framework)
try:
    from .api.serializers import AdvertisementSerializer
    
    class AdvertisementListAPI(generics.ListAPIView):
        queryset = Advertisement.objects.filter(status='published')
        serializer_class = AdvertisementSerializer

    class AdvertisementDetailAPI(generics.RetrieveAPIView):
        queryset = Advertisement.objects.filter(status='published')
        serializer_class = AdvertisementSerializer

    class FavoriteAdvertisementAPI(APIView):
        def post(self, request, pk):
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, 
                              status=status.HTTP_401_UNAUTHORIZED)
            
            ad = get_object_or_404(Advertisement, pk=pk)
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                advertisement=ad
            )
            
            if not created:
                favorite.delete()
                return Response({'status': 'removed'}, status=status.HTTP_200_OK)
            return Response({'status': 'added'}, status=status.HTTP_201_CREATED)
            
except ImportError:
    # Django REST Framework n'est pas installé
    pass


# Vues basées sur les fonctions (alternatives si vous préférez)
@login_required
def advertisement_create_function(request):
    """Version fonction de la création d'annonce"""
    if request.method == 'POST':
        form = AdvertisementForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.author = request.user
            ad.save()
            messages.success(request, 'Annonce créée avec succès!')
            return redirect('publicites:detail', pk=ad.pk)
    else:
        form = AdvertisementForm()
    
    return render(request, 'publicites/create.html', {'form': form})


@login_required
def advertisement_edit_function(request, pk):
    """Version fonction de l'édition d'annonce"""
    ad = get_object_or_404(Advertisement, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Annonce mise à jour avec succès!')
            return redirect('publicites:detail', pk=ad.pk)
    else:
        form = AdvertisementForm(instance=ad)
    
    return render(request, 'publicites/edit.html', {'form': form, 'ad': ad})


@login_required
def advertisement_delete_function(request, pk):
    """Version fonction de la suppression d'annonce"""
    ad = get_object_or_404(Advertisement, pk=pk, author=request.user)
    
    if request.method == 'POST':
        ad.delete()
        messages.success(request, 'Annonce supprimée avec succès!')
        return redirect('publicites:list')
    
    return render(request, 'publicites/delete.html', {'ad': ad})