# urls.py
from django.urls import path
from . import views

app_name = 'ads'

urlpatterns = [
    # ===== URLS POUR LES CATÉGORIES =====
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/<int:category_id>/ads/', views.get_category_ads, name='category_ads'),
    
    # ===== URLS POUR LES ANNONCES =====
    # Liste et recherche
    path('', views.AdListView.as_view(), name='ad_list'),
    path('search/', views.AdListView.as_view(), name='ad_search'),
    
    # CRUD des annonces
    path('create/', views.create_ad, name='create_ad'),
    path('<int:pk>/', views.AdDetailView.as_view(), name='ad_detail'),
    path('<int:pk>/update/', views.update_ad, name='update_ad'),
    path('<int:pk>/delete/', views.delete_ad, name='delete_ad'),
    
    # Mes annonces
    path('my-ads/', views.my_ads, name='my_ads'),
    
    # ===== URLS POUR LES RATINGS =====
    path('<int:ad_pk>/rate/', views.add_rating, name='add_rating'),
    path('rating/<int:rating_pk>/delete/', views.delete_rating, name='delete_rating'),
    
    # ===== URLS POUR LE CONTACT =====
    path('<int:ad_pk>/contact/', views.contact_advertiser, name='contact_advertiser'),
    
    # ===== URLS ADMIN =====
    path('admin/', views.admin_ads, name='admin_ads'),
    path('admin/<int:pk>/status/', views.update_ad_status, name='update_ad_status'),
    path('admin/bulk-actions/', views.bulk_ad_actions, name='bulk_ad_actions'),
]