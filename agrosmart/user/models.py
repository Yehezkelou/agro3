from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('farmer', _('Agriculteur')),
        ('seller', _('Vendeur')),
        ('other', _('Autre')),
    )
    
    user_type = models.CharField(
        _("Type d'utilisateur"),
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='other'
    )
    phone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    address = models.TextField(_("Adresse"), blank=True)
    profile_picture = models.ImageField(
        _("Photo de profil"),
        upload_to='users/profile_pictures/',
        blank=True,
        null=True
    )
    
    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(_("Biographie"), blank=True)
    website = models.URLField(_("Site web"), blank=True)
    location = models.CharField(_("Localisation"), max_length=100, blank=True)
    
    def __str__(self):
        return f"Profil de {self.user.username}"