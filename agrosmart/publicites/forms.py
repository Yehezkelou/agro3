from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Advertisement, AdvertisementImage, Category


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['title', 'description', 'price', 'category', 'status', 'is_premium' ]
        labels = {
            'title': _("Titre"),
            'description': _("Description"),
            'price': _("Prix"),
            'category': _("Catégorie"),
            'status': _("Statut"),
            'is_premium': _("Annonce premium"),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class AdvertisementImageForm(forms.ModelForm):
    class Meta:
        model = AdvertisementImage
        fields = ['image', 'caption', 'is_main']
        labels = {
            'image': _("Image"),
            'caption': _("Légende"),
            'is_main': _("Image principale"),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'name': _("Nom"),
            'description': _("Description"),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class AdvertisementFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label=_("Catégorie"),
        empty_label=_("Toutes les catégories")
    )
    min_price = forms.DecimalField(
        required=False,
        label=_("Prix minimum"),
        decimal_places=2,
        max_digits=10
    )
    max_price = forms.DecimalField(
        required=False,
        label=_("Prix maximum"),
        decimal_places=2,
        max_digits=10
    )
    search = forms.CharField(
        required=False,
        label=_("Recherche"),
        widget=forms.TextInput(attrs={'placeholder': _("Rechercher...")})
    )
    premium_only = forms.BooleanField(
        required=False,
        label=_("Annonces premium seulement")
    )