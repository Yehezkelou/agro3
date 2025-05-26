from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from .forms import (
    UserRegistrationForm, 
    UserUpdateForm, 
    UserProfileForm, 
    CustomAuthenticationForm,
    UserProfilePictureForm,
    PasswordChangeCustomForm
)
from .models import UserProfile, User
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .forms import UserProfilePictureForm  # Import correct

def register(request):
    """Vue d'inscription avec gestion d'erreurs améliorée"""
    if request.user.is_authenticated:
        return redirect('users:profile')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    # Créer automatiquement le profil utilisateur
                    UserProfile.objects.get_or_create(user=user)
                    login(request, user)
                    messages.success(request, _('Inscription réussie! Bienvenue {}'.format(user.username)))
                    return redirect('users:profile')
            except Exception as e:
                messages.error(request, _('Une erreur est survenue lors de l\'inscription.'))
        else:
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = UserRegistrationForm()
    
    return render(request, 'user/register.html', {'form': form})


class CustomLoginView(LoginView):
    """Vue de connexion personnalisée"""
    form_class = CustomAuthenticationForm
    template_name = 'user/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('users:profile')
    
    def form_valid(self, form):
        messages.success(self.request, _('Connexion réussie!'))
        return super().form_valid(form)


@login_required
def profile(request):
    """Vue du profil utilisateur"""
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        # Créer le profil s'il n'existe pas
        profile = UserProfile.objects.create(user=request.user)
    
    context = {
        'user': request.user,
        'profile': profile
    }
    return render(request, 'user/profile.html', context)


@login_required
def edit_profile(request):
    """Vue d'édition du profil avec gestion séparée des formulaires"""
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    profile_form.save()
                    messages.success(request, _('Profil mis à jour avec succès!'))
                    return redirect('users:profile')
            except Exception as e:
                messages.error(request, _('Une erreur est survenue lors de la mise à jour.'))
        else:
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'user/edit_profile.html', context)


@login_required
def change_profile_picture(request):
    """Vue pour changer la photo de profil"""
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfilePictureForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _('Photo de profil mise à jour!'))
                return redirect('users:profile')
            except Exception as e:
                messages.error(request, _('Erreur lors du téléchargement de l\'image.'))
        else:
            messages.error(request, _('Veuillez sélectionner une image valide.'))
    else:
        form = UserProfilePictureForm(instance=profile)
    
    return render(request, 'user/change_picture.html', {'form': form})


@login_required
def change_password(request):
    """Vue pour changer le mot de passe"""
    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.user, request.POST)
        if form.is_valid():
            try:
                new_password = form.cleaned_data['new_password1']
                request.user.set_password(new_password)
                request.user.save()
                # Maintenir la session après changement de mot de passe
                update_session_auth_hash(request, request.user)
                messages.success(request, _('Mot de passe changé avec succès!'))
                return redirect('users:profile')
            except Exception as e:
                messages.error(request, _('Erreur lors du changement de mot de passe.'))
        else:
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = PasswordChangeCustomForm(request.user)
    
    return render(request, 'user/change_password.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def delete_account(request):
    """Vue pour supprimer le compte utilisateur"""
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            try:
                user = request.user
                logout(request)
                user.delete()
                messages.success(request, _('Votre compte a été supprimé avec succès.'))
                return redirect('home')  # Rediriger vers la page d'accueil
            except Exception as e:
                messages.error(request, _('Erreur lors de la suppression du compte.'))
                return redirect('users:profile')
        else:
            messages.error(request, _('Mot de passe incorrect.'))
            return redirect('users:profile')
    
    return redirect('users:profile')


@login_required
def ajax_check_username(request):
    """Vue AJAX pour vérifier la disponibilité d'un nom d'utilisateur"""
    username = request.GET.get('username', '')
    is_available = not User.objects.filter(
        username=username
    ).exclude(pk=request.user.pk).exists()
    
    return JsonResponse({'available': is_available})


@login_required
def ajax_check_email(request):
    """Vue AJAX pour vérifier la disponibilité d'un email"""
    email = request.GET.get('email', '')
    is_available = not User.objects.filter(
        email=email
    ).exclude(pk=request.user.pk).exists()
    
    return JsonResponse({'available': is_available})


def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, _('Vous avez été déconnecté avec succès.'))
    return redirect('publicites:home')  # Ou la page de votre choix


# Vue pour afficher le profil public d'un utilisateur
def public_profile(request, username):
    """Vue du profil public d'un utilisateur"""
    user = get_object_or_404(User, username=username)
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        profile = None
    
    context = {
        'profile_user': user,
        'profile': profile,
        'is_own_profile': request.user == user if request.user.is_authenticated else False
    }
    return render(request, 'user/public_profile.html', context)