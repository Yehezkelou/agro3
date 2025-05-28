from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify

class Culture(models.Model):
    TYPE_CHOICES = [
        ('CEREALE', 'Céréale'),
        ('LEGUME', 'Légume'),
        ('FRUIT', 'Fruit'),
        ('TUBERCULE', 'Tubercule'),
        ('AUTRE', 'Autre'),
    ]
    
    type_culture = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name="Type de culture"
    )

    slug = models.SlugField(unique=True, blank=True)
    nom = models.CharField(max_length=100, unique=True)
    cycle_croissance = models.PositiveIntegerField(help_text="Durée en jours")
    besoin_eau = models.PositiveIntegerField(help_text="Besoin en eau (mm/saison)")
    temperature_ideale = models.CharField(max_length=50, help_text="Plage de température idéale")
    description = models.TextField()
    image = models.ImageField(upload_to='cultures/', null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

class PratiqueAgricole(models.Model):
    SAISON_CHOICES = [
        ('PLUIE', 'Saison des pluies'),
        ('SECHE', 'Saison sèche'),
        ('TOUTE', 'Toute saison'),
    ]
    
    culture = models.ForeignKey(Culture, on_delete=models.CASCADE, related_name='pratiques')
    nom = models.CharField(max_length=200)
    description = models.TextField()
    saison = models.CharField(max_length=20, choices=SAISON_CHOICES)
    avantages = models.TextField()
    difficulte = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Niveau de difficulté (1-5)"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Pratique agricole"
        verbose_name_plural = "Pratiques agricoles"

    def __str__(self):
        return f"{self.nom} ({self.culture.nom})"