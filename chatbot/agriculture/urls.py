from django.urls import path
from . import views

app_name = 'agriculture'

urlpatterns = [
    path('', views.conseils_agricoles, name='conseils'),
    path('cultures/', views.ListeCulturesView.as_view(), name='liste_cultures'),
    path('cultures/<int:pk>/', views.DetailCultureView.as_view(), name='detail_culture'),
    path('pratiques/<str:saison>/', views.PratiquesParSaisonView.as_view(), name='pratiques_saison'),
    path('pratique/<int:pk>/', views.DetailPratiqueView.as_view(), name='detail_pratique'),
]