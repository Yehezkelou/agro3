from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Culture, PratiqueAgricole

class ListeCulturesView(ListView):
    model = Culture
    template_name = 'agriculture/list_cultures.html'
    context_object_name = 'cultures'
    paginate_by = 10

class DetailCultureView(DetailView):
    model = Culture
    template_name = 'agriculture/detail_cultures.html'
    context_object_name = 'culture'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pratiques'] = self.object.pratiques.all()
        return context

class PratiquesParSaisonView(ListView):
    template_name = 'agriculture/pratiques_saison.html'
    context_object_name = 'pratiques'

    def get_queryset(self):
        saison = self.kwargs['saison']
        return PratiqueAgricole.objects.filter(saison=saison).select_related('culture')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['saison'] = self.kwargs['saison']
        return context

def conseils_agricoles(request):
    cultures_populaires = Culture.objects.filter(active=True)[:5]
    pratiques_recentes = PratiqueAgricole.objects.order_by('-date_creation')[:5]
    
    # Récupérer tous les types de culture disponibles
    culture_types = Culture.TYPE_CHOICES  # Accès aux choix définis dans le modèle

    return render(request, 'agriculture/conseils.html', {
        'cultures_populaires': cultures_populaires,
        'pratiques_recentes': pratiques_recentes,
        'culture_types': culture_types,  # Ajouté
        'saisons': PratiqueAgricole.SAISON_CHOICES,
    })


class DetailPratiqueView(DetailView):
    model = PratiqueAgricole
    template_name = 'agriculture/detail_pratique.html'
    context_object_name = 'pratique'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajoutez des données supplémentaires si nécessaire
        return context