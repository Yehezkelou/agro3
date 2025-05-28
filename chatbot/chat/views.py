from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Conversation, Message
from .utils import AgroChatbot
from agriculture.models import Culture, PratiqueAgricole
import json

@login_required
def chatbot_interface(request):
    conversations = Conversation.objects.filter(utilisateur=request.user).order_by('-date_derniere_activite')
    return render(request, 'chatbot/chatbot_interface.html', {
        'conversations': conversations,
        'cultures': Culture.objects.all()[:5]
    })

@login_required
def chat_api(request):
    if request.method == 'POST':
      try:
            data = json.loads(request.body)
            user_input = data.get('message')
            conversation_id = data.get('conversation_id')

            if not user_input:
                return JsonResponse({'error': 'Message vide'}, status=400)


            chatbot = AgroChatbot(user=request.user)
            if conversation_id:
                conversation = Conversation.objects.get(id=conversation_id, utilisateur=request.user)
            else:
                conversation = Conversation.objects.create(utilisateur=request.user)

        # Sauvegarder le message de l'utilisateur
            user_message = Message.objects.create(
            conversation=conversation,
            texte=user_input,
            est_utilisateur=True
        )
            chatbot = AgroChatbot(user=request.user)
        # Générer la réponse du chatbot
            bot_response = chatbot.generate_response(user_input, conversation)
        
        # Sauvegarder la réponse du bot
            bot_message = Message.objects.create(
            conversation=conversation,
            texte=bot_response,
            est_utilisateur=False
        )
        
            return JsonResponse({
            'response': bot_response,
            'conversation_id': conversation.id
        })
    
      except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)