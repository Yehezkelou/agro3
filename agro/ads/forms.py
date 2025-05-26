# forms.py
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .models import Ad, Category, AdImage, AdRating, CustomUser


class CategoryForm(forms.ModelForm):
    """Formulaire pour créer/modifier une catégorie"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la catégorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description de la catégorie'
            }),
            'icon': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Une catégorie avec ce nom existe déjà.")
        return name


class AdForm(forms.ModelForm):
    """Formulaire pour créer/modifier une annonce"""
    
    class Meta:
        model = Ad
        fields = ['title', 'description', 'category', 'location', 'price', 
                 'campaign_start', 'campaign_end']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de l\'annonce'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Description détaillée de votre annonce'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Localisation'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prix (optionnel)',
                'step': '0.01'
            }),
            'campaign_start': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'campaign_end': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les catégories actives
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        
        # Définir des dates par défaut
        if not self.instance.pk:
            now = datetime.now()
            self.fields['campaign_start'].initial = now
            self.fields['campaign_end'].initial = now + timedelta(days=30)

    def clean(self):
        cleaned_data = super().clean()
        campaign_start = cleaned_data.get('campaign_start')
        campaign_end = cleaned_data.get('campaign_end')

        if campaign_start and campaign_end:
            if campaign_start >= campaign_end:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")
            
            if campaign_start < datetime.now():
                raise ValidationError("La date de début ne peut pas être dans le passé.")
            
            # Vérifier la durée maximale (par exemple 365 jours)
            if (campaign_end - campaign_start).days > 365:
                raise ValidationError("La campagne ne peut pas durer plus de 365 jours.")
        
        return cleaned_data

    def save(self, commit=True):
        ad = super().save(commit=False)
        if self.user:
            ad.author = self.user
        if commit:
            ad.save()
        return ad


class AdImageForm(forms.ModelForm):
    """Formulaire pour ajouter des images à une annonce"""
    
    class Meta:
        model = AdImage
        fields = ['image', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > 5 * 1024 * 1024:  # 5MB
            raise ValidationError("L'image ne doit pas dépasser 5MB.")
        return image


# Formset pour gérer plusieurs images
AdImageFormSet = inlineformset_factory(
    Ad, AdImage,
    form=AdImageForm,
    fields=['image', 'is_primary'],
    extra=3,
    max_num=10,
    can_delete=True,
    widgets={
        'image': forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        'is_primary': forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
    }
)


class AdRatingForm(forms.ModelForm):
    """Formulaire pour noter une annonce"""
    
    class Meta:
        model = AdRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Votre commentaire (optionnel)'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.ad = kwargs.pop('ad', None)
        super().__init__(*args, **kwargs)
        
        # Personnaliser les choix de rating
        self.fields['rating'].choices = [
            (5, '⭐⭐⭐⭐⭐ Excellent'),
            (4, '⭐⭐⭐⭐ Très bien'),
            (3, '⭐⭐⭐ Bien'),
            (2, '⭐⭐ Moyen'),
            (1, '⭐ Mauvais'),
        ]

    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier que l'utilisateur n'a pas déjà noté cette annonce
        if self.user and self.ad:
            if AdRating.objects.filter(user=self.user, ad=self.ad).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Vous avez déjà noté cette annonce.")
            
            # Vérifier que l'utilisateur ne note pas sa propre annonce
            if self.ad.author == self.user:
                raise ValidationError("Vous ne pouvez pas noter votre propre annonce.")
        
        return cleaned_data

    def save(self, commit=True):
        rating = super().save(commit=False)
        if self.user:
            rating.user = self.user
        if self.ad:
            rating.ad = self.ad
        if commit:
            rating.save()
        return rating


class AdSearchForm(forms.Form):
    """Formulaire de recherche d'annonces"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher une annonce...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Localisation'
        })
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix min'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix max'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(Ad.STATUSES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    author_type = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(CustomUser.USER_TYPES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')

        if min_price and max_price and min_price > max_price:
            raise ValidationError("Le prix minimum ne peut pas être supérieur au prix maximum.")
        
        return cleaned_data


class AdStatusForm(forms.ModelForm):
    """Formulaire pour modifier le statut d'une annonce (admin)"""
    
    class Meta:
        model = Ad
        fields = ['status', 'is_featured']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class BulkAdActionForm(forms.Form):
    """Formulaire pour actions en lot sur les annonces"""
    
    ACTION_CHOICES = [
        ('approve', 'Approuver'),
        ('reject', 'Rejeter'),
        ('feature', 'Mettre en vedette'),
        ('unfeature', 'Retirer de la vedette'),
        ('delete', 'Supprimer'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    selected_ads = forms.CharField(
        widget=forms.HiddenInput()
    )

    def clean_selected_ads(self):
        selected_ads = self.cleaned_data.get('selected_ads')
        if not selected_ads:
            raise ValidationError("Aucune annonce sélectionnée.")
        
        try:
            ad_ids = [int(id) for id in selected_ads.split(',') if id.strip()]
            if not ad_ids:
                raise ValidationError("Aucune annonce sélectionnée.")
            return ad_ids
        except (ValueError, TypeError):
            raise ValidationError("Sélection d'annonces invalide.")


class ContactAdvertiserForm(forms.Form):
    """Formulaire pour contacter l'auteur d'une annonce"""
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sujet du message'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Votre message'
        })
    )
    phone = forms.CharField(
        required=False,
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre numéro de téléphone (optionnel)'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.ad = kwargs.pop('ad', None)
        super().__init__(*args, **kwargs)
        
        # Pré-remplir le sujet si on a l'annonce
        if self.ad and not self.initial.get('subject'):
            self.initial['subject'] = f"Concernant votre annonce: {self.ad.title}"