document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const newConversationBtn = document.getElementById('new-conversation');
    const conversationItems = document.querySelectorAll('.conversation-item');
    const conversationTitle = document.getElementById('conversation-title');
    
    let currentConversationId = null;
    
    // Charger une conversation
    conversationItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Mettre en surbrillance la conversation sélectionnée
            conversationItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            const conversationId = this.getAttribute('data-id');
            loadConversation(conversationId);
        });
    });
    
    // Nouvelle conversation
    newConversationBtn.addEventListener('click', function() {
        conversationItems.forEach(i => i.classList.remove('active'));
        currentConversationId = null;
        conversationTitle.textContent = 'Nouvelle conversation';
        chatMessages.innerHTML = `
            <div class="alert alert-info text-center">
                Nouvelle conversation commencée. Posez votre question à AgroBot.
            </div>
        `;
    });
    
    // Modifiez la fonction sendMessage dans chatbot.js
function sendMessage() {
    const message = userInput.value.trim();
    if (message === '') return;
    
    // Afficher le message de l'utilisateur immédiatement
    addMessage(message, 'user');
    userInput.value = '';
    
    // Afficher un indicateur de typing
    const typingIndicator = document.createElement('div');
    typingIndicator.id = 'typing-indicator';
    typingIndicator.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Envoyer au serveur
    fetch('/chatbot/api/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            message: message,
            conversation_id: currentConversationId
        })
    })
    .then(response => response.json())
    .then(data => {
        // Supprimer l'indicateur de typing
        document.getElementById('typing-indicator')?.remove();
        
        if (data.error) {
            addMessage("Désolé, une erreur s'est produite.", 'bot');
            return;
        }
        
        if (!currentConversationId && data.conversation_id) {
            currentConversationId = data.conversation_id;
            conversationTitle.textContent = `Conversation #${currentConversationId}`;
        }
        
        addMessage(data.response, 'bot');
    })
    .catch(error => {
        document.getElementById('typing-indicator')?.remove();
        addMessage("Désolé, je n'ai pas pu traiter votre demande.", 'bot');
    });
}
    
    // Gestion des événements
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Fonctions utilitaires
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function loadConversation(conversationId) {
        // TODO: Implémenter le chargement des messages existants via API
        currentConversationId = conversationId;
        conversationTitle.textContent = `Conversation #${conversationId}`;
        chatMessages.innerHTML = `
            <div class="alert alert-info text-center">
                Chargement de la conversation...
            </div>
        `;
        
        // Simuler le chargement
        setTimeout(() => {
            // Remplacer par un appel API réel
            chatMessages.innerHTML = `
                <div class="alert alert-success text-center">
                    Conversation #${conversationId} chargée. Continuez votre discussion.
                </div>
            `;
        }, 500);
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});