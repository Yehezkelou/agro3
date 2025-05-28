from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Interface Web
    path('', login_required(views.chatbot_interface), name='interface'),
    # Endpoints API
    path('api/', login_required(views.chat_api), name='api'),

]   