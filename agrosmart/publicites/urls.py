from django.urls import path
from . import views

app_name = 'publicites'

urlpatterns = [
    # Pages principales
    path('', views.home_view, name='home'),
    path('list/', views.AdvertisementListView.as_view(), name='list'),
    path('<int:pk>/', views.AdvertisementDetailView.as_view(), name='detail'),
    
    # Gestion des annonces
    path('create/', views.AdvertisementCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.AdvertisementEditView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.AdvertisementDeleteView.as_view(), name='delete'),
    
    # Gestion des images
    path('<int:pk>/images/', views.AdvertisementImageView.as_view(), name='images'),
    path('<int:pk>/images/<int:image_pk>/delete/', views.advertisement_image_delete, name='image_delete'),
    
    # Favoris (vues fonction)
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorite_list, name='favorites'),
    
    # Catégories (à implémenter si nécessaire)
    # path('categories/', views.CategoryListView.as_view(), name='category_list'),
    # path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # API REST (optionnel - seulement si Django REST Framework est installé)
    path('api/', views.AdvertisementListAPI.as_view(), name='api_list'),
    path('api/<int:pk>/', views.AdvertisementDetailAPI.as_view(), name='api_detail'),
    path('api/<int:pk>/favorite/', views.FavoriteAdvertisementAPI.as_view(), name='api_toggle_favorite'),
]


# Alternative avec URLs basées sur date/slug (si vos modèles supportent cela)
# Décommentez et remplacez les URLs ci-dessus si vous voulez garder ce système
