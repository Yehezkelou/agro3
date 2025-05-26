from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from user.models import User
import datetime

class Category(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")
        ordering = ('name',)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Advertisement(models.Model):
    STATUS_CHOICES = (
        ('draft', _('Brouillon')),
        ('published', _('Publié')),
        ('archived', _('Archivé')),
    )
    
    # Informations principales
    title = models.CharField(_("Titre"), max_length=200)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(_("Description"))
    price = models.DecimalField(
        _("Prix"),
        max_digits=10,
        decimal_places=2
    )
    
    # Relations
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='advertisements',  # Changé de 'ads' pour plus de clarté
        verbose_name=_("Catégorie")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='advertisements',  # Changé de 'ads' pour plus de clarté
        verbose_name=_("Auteur")
    )
    
    # Dates - utilisation cohérente
    created_at = models.DateTimeField(default=datetime.datetime.now)
    updated_at = models.DateTimeField(default=datetime.datetime.now)
    
    # Statut et options
    status = models.CharField(
        _("Statut"),
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_premium = models.BooleanField(_("Annonce premium"), default=False)
    
    class Meta:
        ordering = ('-created_at',)  # Utilisation cohérente de created_at
        verbose_name = _("Annonce")
        verbose_name_plural = _("Annonces")
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['is_premium']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('publicites:detail', kwargs={'pk': self.pk})
    
    @property
    def main_image(self):
        """Retourne l'image principale ou la première image"""
        main_img = self.images.filter(is_main=True).first()
        if main_img:
            return main_img
        return self.images.first()
    
    @property
    def is_published(self):
        return self.status == 'published'
    
    def get_price_display(self):
        """Affichage formaté du prix"""
        return f"{self.price} €"


class AdvertisementImage(models.Model):
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("Annonce")
    )
    image = models.ImageField(
        _("Image"),
        upload_to='publicites/images/%Y/%m/'  # Organisation par année/mois
    )
    caption = models.CharField(_("Légende"), max_length=200, blank=True)
    is_main = models.BooleanField(_("Image principale"), default=False)
    created_at = models.DateTimeField(_("Date d'ajout"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Image d'annonce")
        verbose_name_plural = _("Images d'annonce")
        ordering = ('-is_main', 'created_at')
    
    def __str__(self):
        return f"Image pour {self.advertisement.title}"
    
    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule image principale par annonce
        if self.is_main:
            AdvertisementImage.objects.filter(
                advertisement=self.advertisement,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_("Utilisateur")
    )
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='favorite',  # Changé pour correspondre au service
        verbose_name=_("Annonce")
    )
    created_at = models.DateTimeField(_("Date d'ajout"), auto_now_add=True)  # Changé pour cohérence
    
    class Meta:
        unique_together = ('user', 'advertisement')
        verbose_name = _("Favori")
        verbose_name_plural = _("Favoris")
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"{self.user.username} aime {self.advertisement.title}"


# Modèle supplémentaire pour les vues (optionnel)
class AdvertisementView(models.Model):
    """Modèle pour tracker les vues des annonces"""
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='advertisement_views'
    )
    ip_address = models.GenericIPAddressField()
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Vue d'annonce")
        verbose_name_plural = _("Vues d'annonce")
        unique_together = ('advertisement', 'ip_address')  # Une vue par IP par annonce
    
    def __str__(self):
        return f"Vue de {self.advertisement.title}"


# Signal pour auto-générer le slug
from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=Advertisement)
def generate_unique_slug(sender, instance, **kwargs):
    """Génère un slug unique pour les annonces"""
    if not instance.slug:
        base_slug = slugify(instance.title)
        slug = base_slug
        counter = 1
        
        while Advertisement.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug

@receiver(pre_save, sender=Category)
def generate_category_slug(sender, instance, **kwargs):
    """Génère un slug unique pour les catégories"""
    if not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        
        while Category.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug