# urls.py
from django.urls import path
from . import views
app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profil utilisateur
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/delete-picture/', views.delete_profile_picture, name='delete_profile_picture'),
    path('profile/change-type/', views.change_user_type, name='change_user_type'),
    
    # Vues publiques
    path('user/<str:username>/', views.UserDetailView.as_view(), name='user_detail'),
    path('farmers/', views.FarmerListView.as_view(), name='farmer_list'),
    path('advertisers/', views.AdvertiserListView.as_view(), name='advertiser_list'),
    
    # Recherche
    path('search/', views.search_users, name='search_users'),
    
    # Administration
    path('admin/user/<int:pk>/update/', views.AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('admin/user/<int:user_id>/toggle-verification/', views.toggle_verification, name='toggle_verification'),
]