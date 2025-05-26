# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import CustomUser
from .forms import (
    CustomUserCreationForm, 
    CustomLoginForm, 
    ProfileUpdateForm,
    CustomUserChangeForm
)


class RegisterView(CreateView):
    """Vue d'inscription"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Votre compte a été créé avec succès!')
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)
            
            # Gérer "Se souvenir de moi"
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username}!')
            
            # Redirection après connexion
            next_page = request.GET.get('next', 'accounts:profile')
            return redirect(next_page)
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, DetailView):
    """Vue du profil utilisateur"""
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'

    def get_object(self):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Vue de mise à jour du profil"""
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Votre profil a été mis à jour avec succès!')
        return response


class UserDetailView(DetailView):
    """Vue détaillée d'un utilisateur (public)"""
    model = CustomUser
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_profile'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_own_profile'] = self.request.user == self.object
        return context


class FarmerListView(ListView):
    """Liste des agriculteurs"""
    model = CustomUser
    template_name = 'accounts/farmer_list.html'
    context_object_name = 'farmers'
    paginate_by = 12

    def get_queryset(self):
        return CustomUser.objects.filter(
            user_type='farmer',
            is_active=True
        ).order_by('-date_joined')


class AdvertiserListView(ListView):
    """Liste des annonceurs"""
    model = CustomUser
    template_name = 'accounts/advertiser_list.html'
    context_object_name = 'advertisers'
    paginate_by = 12

    def get_queryset(self):
        return CustomUser.objects.filter(
            user_type='advertiser',
            is_active=True
        ).order_by('-date_joined')


@login_required
def delete_profile_picture(request):
    """Supprimer la photo de profil"""
    if request.method == 'POST':
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete()
            user.save()
            messages.success(request, 'Photo de profil supprimée avec succès.')
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Aucune photo à supprimer.'})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
def change_user_type(request):
    """Changer le type d'utilisateur"""
    if request.method == 'POST':
        new_type = request.POST.get('user_type')
        
        if new_type in dict(CustomUser.USER_TYPES):
            request.user.user_type = new_type
            request.user.save()
            
            type_name = dict(CustomUser.USER_TYPES)[new_type]
            messages.success(
                request, 
                f'Votre type de compte a été changé vers "{type_name}".'
            )
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Type d\'utilisateur invalide.'
            })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


def search_users(request):
    """Recherche d'utilisateurs (AJAX)"""
    query = request.GET.get('q', '')
    user_type = request.GET.get('type', '')
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    users = CustomUser.objects.filter(
        is_active=True
    ).filter(
        username__icontains=query
    ) | CustomUser.objects.filter(
        is_active=True
    ).filter(
        first_name__icontains=query
    ) | CustomUser.objects.filter(
        is_active=True
    ).filter(
        last_name__icontains=query
    )
    
    if user_type:
        users = users.filter(user_type=user_type)
    
    users = users.distinct()[:10]
    
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'user_type': user.get_user_type_display(),
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'location': user.location,
        })
    
    return JsonResponse({'users': users_data})


class AdminUserUpdateView(LoginRequiredMixin, UpdateView):
    """Vue admin pour modifier un utilisateur"""
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/admin_user_update.html'
    context_object_name = 'user_profile'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Vous n'avez pas les permissions nécessaires.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('user_detail', kwargs={'username': self.object.username})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Utilisateur mis à jour avec succès!')
        return response


@login_required
def toggle_verification(request, user_id):
    """Basculer le statut de vérification d'un utilisateur (admin seulement)"""
    if not request.user.is_staff:
        raise PermissionDenied("Vous n'avez pas les permissions nécessaires.")
    
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_verified = not user.is_verified
    user.save()
    
    status = "vérifié" if user.is_verified else "non vérifié"
    messages.success(
        request, 
        f'L\'utilisateur {user.username} est maintenant {status}.'
    )
    
    return redirect('user_detail', username=user.username)
# Create your views here.
