from django.urls import path
from . import views

app_name = 'formations'

urlpatterns = [
    # Liste et recherche
    path('', views.formation_list, name='list'),
    path('search/', views.search_formations_ajax, name='search_ajax'),
    
    # Catégories
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Détail et contenu des formations
    path('<slug:slug>/', views.formation_detail, name='detail'),
    path('<slug:slug>/content/', views.formation_content, name='content'),
    
    # Actions utilisateur
    path('<slug:slug>/enroll/', views.enroll_formation, name='enroll'),
    path('<slug:slug>/progress/', views.update_progress, name='update_progress'),
    path('<slug:slug>/review/', views.submit_review, name='submit_review'),
    
    # Espace utilisateur
    path('my/formations/', views.my_formations, name='my_formations'),
    
    # URLs alternatives avec vues basées sur les classes
    path('cbv/list/', views.FormationListView.as_view(), name='list_cbv'),
    path('cbv/<slug:slug>/', views.FormationDetailView.as_view(), name='detail_cbv'),
]