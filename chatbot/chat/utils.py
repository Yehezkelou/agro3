from .gemini_service import GeminiService
from .models import Message
from django.contrib.auth import get_user_model

User = get_user_model()

class AgroChatbot:
    def __init__(self, user=None):
        self.user = user
        self.gemini = GeminiService()
    
    def generate_response(self, user_input, conversation=None):
        # Récupérer l'historique de conversation si disponible
        history = None
        if conversation:
            messages = Message.objects.filter(conversation=conversation).order_by('date_creation')[:10]
            history = [{
                'texte': msg.texte,
                'est_utilisateur': msg.est_utilisateur
            } for msg in messages]
        
        # Générer la réponse avec Gemini
        return self.gemini.generate_response(user_input, history)