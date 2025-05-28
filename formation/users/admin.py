from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'get_full_name', 'user_type', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations professionnelles', {'fields': ('user_type', 'phone', 'location')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)