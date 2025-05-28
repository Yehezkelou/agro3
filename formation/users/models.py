from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('FARMER', 'Agriculteur'),
        ('EXPERT', 'Expert Agricole'),
        ('ADMIN', 'Administrateur'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='FARMER')
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"