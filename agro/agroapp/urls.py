# core/urls.py
from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('categories/', views.category_list, name='categories'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('statistics/', views.statistics, name='statistics'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
]