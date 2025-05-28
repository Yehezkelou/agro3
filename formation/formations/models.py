from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from users.models import CustomUser
from django.utils import timezone


class FormationCategory(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom"),
        help_text=_("Nom de la catégorie de formation")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée de la catégorie")
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly version du nom")
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Icône"),
        help_text=_("Classe CSS de l'icône (ex: fa-code)")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Catégorie de formation")
        verbose_name_plural = _("Catégories de formation")
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('formations:category_detail', kwargs={'slug': self.slug})

    @property
    def formation_count(self):
        return self.formation_set.filter(is_active=True).count()
    
    @formation_count.setter
    def formation_count(self, value):
       """
       Setter pour formation_count - empêche l'assignation directe
       car cette valeur est calculée dynamiquement
       """
       raise AttributeError(
        "Cannot set 'formation_count' - this is a computed property based on active formations"
    )


class Formation(models.Model):
    DIFFICULTY_LEVELS = (
        ('DEBUTANT', _('Débutant')),
        ('INTERMEDIAIRE', _('Intermédiaire')),
        ('AVANCE', _('Avancé')),
        ('EXPERT', _('Expert')),
    )

    STATUS_CHOICES = (
        ('DRAFT', _('Brouillon')),
        ('PUBLISHED', _('Publié')),
        ('ARCHIVED', _('Archivé')),
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre"),
        help_text=_("Titre de la formation")
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        verbose_name=_("Slug")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description détaillée de la formation")
    )
    short_description = models.CharField(
        max_length=300,
        verbose_name=_("Description courte"),
        help_text=_("Résumé de la formation (max 300 caractères)"),
        default= "pas de description courte fournie",  # Default value for short description
    )
    category = models.ForeignKey(
        FormationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='formation',
        verbose_name=_("Catégorie")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Prix (CFA)"),
        help_text=_("Prix en francs CFA")
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Prix original"),
        help_text=_("Prix avant réduction")
    )
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_("Durée"),
        help_text=_("Durée en heures")
    )
    difficulty = models.CharField(
        max_length=13,
        choices=DIFFICULTY_LEVELS,
        default='DEBUTANT',
        verbose_name=_("Niveau de difficulté")
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name=_("Statut")
    )
    
    # Contenu multimédia
    video_url = models.URLField(
        blank=True,
        verbose_name=_("URL vidéo"),
        help_text=_("Lien vers la vidéo de présentation")
    )
    thumbnail = models.ImageField(
        upload_to='formations/thumbnails/',
        blank=True,
        verbose_name=_("Miniature"),
        help_text=_("Image de couverture de la formation")
    )
    pdf_content = models.FileField(
        upload_to='formations/pdfs/',
        blank=True,
        verbose_name=_("Contenu PDF"),
        help_text=_("Fichier PDF du contenu de formation")
    )
    
    # Métadonnées SEO
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name=_("Meta description"),
        help_text=_("Description pour les moteurs de recherche")
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Meta mots-clés"),
        help_text=_("Mots-clés séparés par des virgules")
    )
    
    # Statistiques et paramètres
    max_students = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Nombre maximum d'étudiants"),
        help_text=_("Laisser vide pour illimité")
    )
    prerequisites = models.TextField(
        blank=True,
        verbose_name=_("Prérequis"),
        help_text=_("Prérequis nécessaires pour suivre cette formation")
    )
    learning_objectives = models.TextField(
        blank=True,
        verbose_name=_("Objectifs d'apprentissage"),
        help_text=_("Ce que l'étudiant apprendra")
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de publication")
    )
    
    # Flags
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("En vedette"),
        help_text=_("Afficher dans les formations mises en avant")
    )
    is_free = models.BooleanField(
        default=False,
        verbose_name=_("Gratuit"),
        help_text=_("Formation gratuite")
    )

    class Meta:
        verbose_name = _("Formation")
        verbose_name_plural = _("Formations")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()}) - {self.price} CFA"

    def get_absolute_url(self):
        return reverse('formation:detail', kwargs={'slug': self.slug})

    @property
    def is_on_sale(self):
        """Vérifie si la formation est en promotion"""
        return self.original_price and self.original_price > self.price

    @property
    def discount_percentage(self):
        """Calcule le pourcentage de réduction"""
        if self.is_on_sale:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    @property
    def enrolled_count(self):
        """Nombre d'étudiants inscrits"""
        return self.userformation_set.filter(payment_status=True).count()

    @property
    def is_full(self):
        """Vérifie si la formation est complète"""
        if self.max_students:
            return self.enrolled_count >= self.max_students
        return False

    @property
    def completion_rate(self):
        """Taux de complétion de la formation"""
        total_enrolled = self.enrolled_count
        if total_enrolled == 0:
            return 0
        completed = self.userformation_set.filter(
            payment_status=True, completed=True
        ).count()
        return int((completed / total_enrolled) * 100)

    def save(self, *args, **kwargs):
        # Auto-génération du slug si non fourni
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        
        # Mise à jour de la date de publication
        if self.status == 'PUBLISHED' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)


class UserFormation(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('PENDING', _('En attente')),
        ('COMPLETED', _('Complété')),
        ('FAILED', _('Échoué')),
        ('REFUNDED', _('Remboursé')),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_("Utilisateur")
    )
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        verbose_name=_("Formation")
    )
    date_enrolled = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'inscription")
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        verbose_name=_("Statut du paiement")
    )
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Méthode de paiement"),
        help_text=_("Ex: Orange Money, MTN Mobile Money, etc.")
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("ID de transaction"),
        help_text=_("Identifiant de la transaction de paiement")
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Montant payé")
    )
    
    # Progression
    completed = models.BooleanField(
        default=False,
        verbose_name=_("Terminé")
    )
    completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de completion")
    )
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        verbose_name=_("Pourcentage de progression")
    )
    
    # Évaluation
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Note"),
        help_text=_("Note de 1 à 5 étoiles")
    )
    review = models.TextField(
        blank=True,
        verbose_name=_("Avis"),
        help_text=_("Commentaire sur la formation")
    )
    review_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de l'avis")
    )
    
    # Certificat
    certificate_issued = models.BooleanField(
        default=False,
        verbose_name=_("Certificat émis")
    )
    certificate_url = models.URLField(
        blank=True,
        verbose_name=_("URL du certificat")
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Inscription utilisateur")
        verbose_name_plural = _("Inscriptions utilisateur")
        unique_together = ('user', 'formation')
        ordering = ['-date_enrolled']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['formation', 'payment_status']),
            models.Index(fields=['-date_enrolled']),
        ]

    def __str__(self):
        return f"{self.user} - {self.formation.title}"

    @property
    def is_paid(self):
        """Vérifie si le paiement est complété"""
        return self.payment_status == 'COMPLETED'

    @property
    def can_access_content(self):
        """Vérifie si l'utilisateur peut accéder au contenu"""
        return self.is_paid or self.formation.is_free

    def mark_as_completed(self):
        """Marque la formation comme terminée"""
        if not self.completed:
            from django.utils import timezone
            self.completed = True
            self.completion_date = timezone.now()
            self.progress_percentage = 100
            self.save(update_fields=['completed', 'completion_date', 'progress_percentage'])

    def update_progress(self, percentage):
        """Met à jour le pourcentage de progression"""
        if 0 <= percentage <= 100:
            self.progress_percentage = percentage
            if percentage == 100 and not self.completed:
                self.mark_as_completed()
            else:
                self.save(update_fields=['progress_percentage'])


class FormationReview(models.Model):
    """Modèle séparé pour les avis détaillés"""
    user_formation = models.OneToOneField(
        UserFormation,
        on_delete=models.CASCADE,
        verbose_name=_("Inscription")
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Note")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre de l'avis")
    )
    content = models.TextField(
        verbose_name=_("Contenu de l'avis")
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Avis vérifié"),
        help_text=_("Avis d'un utilisateur ayant complété la formation")
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_("Approuvé"),
        help_text=_("Avis approuvé pour publication")
    )
    helpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de votes utiles")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Avis de formation")
        verbose_name_plural = _("Avis de formations")
        ordering = ['-created_at']

    def __str__(self):
        return f"Avis de {self.user_formation.user} sur {self.user_formation.formation.title}"