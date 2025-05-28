import requests 
import json
from django.conf import settings
from django.core.cache import cache
from agriculture.models import PratiqueAgricole, Culture

class GeminiService:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.context = self._build_context()
    
    def _build_context(self):
        """Construit le contexte agricole pour le prompt"""
        pratiques = PratiqueAgricole.objects.all()[:10]
        cultures = Culture.objects.all()[:10]
        
        context = {
            "role": "user",
            "parts": [{
                "text": f"""Tu es AgroBot, un assistant expert en agriculture. 
                Voici des informations clés:
                Cultures: {", ".join([c.nom for c in cultures])}
                Pratiques: {"".join([f"- {p.nom} ({p.culture.nom}): {p.description[:100]}...\\n" for p in pratiques])}
                Conseils: 
                - Sois concis et technique
                - Adapte tes réponses au climat de la cote d'ivoire
                - Utilise un langage simple
                - reponse en toute langue et langue ethnique
                - reponse sur toute la culture ivoirienne
                - Donne des conseils actionnables"""
            }]
        }
        return context
    
    def generate_response(self, user_input, history=None):
        try:
            messages = []
            
            # Ajoute le contexte système
            messages.append(self.context)
            
            # Ajoute l'historique si disponible
            if history:
                for msg in history:
                    role = "user" if msg['est_utilisateur'] else "model"
                    messages.append({
                        "role": role,
                        "parts": [{"text": msg['texte']}]
                    })
            
            # Ajoute la nouvelle question
            messages.append({
                "role": "user",
                "parts": [{"text": user_input}]
            })
            
            payload = {
                "contents": messages,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500
                }
            }
            
            response = requests.post(
                f"{self.BASE_URL}?key={self.api_key}",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )

            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"Erreur Gemini API: {response.text}")
                return "Je rencontre des difficultés techniques. Veuillez réessayer plus tard."
                
        except Exception as e:
            print(f"Exception: {str(e)}")
            return "Désolé, je n'ai pas pu traiter votre demande."