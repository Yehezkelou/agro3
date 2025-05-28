from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from agriculture.models import Culture, PratiqueAgricole

class Conversation(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_derniere_activite = models.DateTimeField(auto_now=True)
    sujet = models.CharField(max_length=100, blank=True, null=True)
    termine = models.BooleanField(default=False)

    def __str__(self):
        return f"Conversation {self.id} - {self.utilisateur.username}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    texte = models.TextField()
    est_utilisateur = models.BooleanField()
    date_creation = models.DateTimeField(auto_now_add=True)
    references = models.ManyToManyField(PratiqueAgricole, blank=True)

    class Meta:
        ordering = ['date_creation']

    def __str__(self):
        return f"Message {self.id} - {'User' if self.est_utilisateur else 'Bot'}"