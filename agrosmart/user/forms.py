from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import User, UserProfile


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'required': True,
            'class': 'form-control',
            'placeholder': _("Votre adresse email")
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'user_type')
        labels = {
            'user_type': _("Type d'utilisateur"),
            'username': _("Nom d'utilisateur"),
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Votre nom d'utilisateur")
            }),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes CSS aux champs de mot de passe
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _("Mot de passe")
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _("Confirmez le mot de passe")
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Un utilisateur avec cet email existe déjà."))
        return email.lower()


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire de connexion personnalisé avec styling"""
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre nom d'utilisateur")
        })
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre mot de passe")
        })
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('bio', 'website', 'location')
        labels = {
            'bio': _("Biographie"),
            'website': _("Site web"),
            'location': _("Localisation"),
        }
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _("Parlez-nous de vous...")
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _("https://votre-site.com")
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Votre ville, pays")
            }),
        }
    
    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website


class UserUpdateForm(UserChangeForm):
    password = None  # On ne gère pas le mot de passe ici
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        labels = {
            'first_name': _("Prénom"),
            'last_name': _("Nom"),
            'username': _("Nom d'utilisateur"),
            'email': _("Email"),
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Vérifier que l'email n'est pas déjà utilisé par un autre utilisateur
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Un autre utilisateur utilise déjà cet email."))
        return email.lower()


class UserProfilePictureForm(forms.ModelForm):
    """Formulaire séparé pour la photo de profil"""
    class Meta:
        model = User
        fields = ['profile_picture']
        labels = {
            'profile_picture': _("Photo de profil"),
        }
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            # Vérifier la taille du fichier (max 5MB)
            if picture.size > 5 * 1024 * 1024:
                raise ValidationError(_("L'image ne doit pas dépasser 5MB."))
            
            # Vérifier le type de fichier
            if not picture.content_type.startswith('image/'):
                raise ValidationError(_("Le fichier doit être une image."))
        
        return picture


class PasswordChangeCustomForm(forms.Form):
    """Formulaire personnalisé pour changer le mot de passe"""
    old_password = forms.CharField(
        label=_("Mot de passe actuel"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre mot de passe actuel")
        })
    )
    new_password1 = forms.CharField(
        label=_("Nouveau mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nouveau mot de passe")
        })
    )
    new_password2 = forms.CharField(
        label=_("Confirmez le nouveau mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Confirmez le nouveau mot de passe")
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError(_("Le mot de passe actuel est incorrect."))
        return old_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError(_("Les nouveaux mots de passe ne correspondent pas."))
        
        return cleaned_data