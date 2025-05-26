from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Ad, AdImage, AdRating


class AdImageInline(admin.TabularInline):
    model = AdImage
    extra = 1
    fields = ('image', 'is_primary', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px;"/>',
                obj.image.url
            )
        return "-"
    image_preview.short_description = 'Aperçu'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'ad_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def ad_count(self, obj):
        return obj.ad_set.count()
    ad_count.short_description = "Nombre d'annonces"


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'category', 'status', 
        'is_featured', 'views_count', 'created_at', 
        'days_remaining'
    )
    list_filter = (
        'status', 'is_featured', 'category', 
        'author__user_type', 'created_at'
    )
    search_fields = ('title', 'description', 'author__username')
    date_hierarchy = 'created_at'
    inlines = (AdImageInline,)
    readonly_fields = ('views_count', 'created_at', 'updated_at')
    list_editable = ('status', 'is_featured')
    actions = ['approve_ads', 'reject_ads', 'feature_ads']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'description', 'category', 'author')
        }),
        ('Détails', {
            'fields': ('location', 'price')
        }),
        ('Dates', {
            'fields': ('campaign_start', 'campaign_end')
        }),
        ('Statut', {
            'fields': ('status', 'is_featured')
        }),
        ('Métadonnées', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Jours restants'
    
    def approve_ads(self, request, queryset):
        queryset.update(status='approved')
    approve_ads.short_description = "Approuver les annonces sélectionnées"
    
    def reject_ads(self, request, queryset):
        queryset.update(status='rejected')
    reject_ads.short_description = "Rejeter les annonces sélectionnées"
    
    def feature_ads(self, request, queryset):
        queryset.update(is_featured=True)
    feature_ads.short_description = "Mettre en vedette les annonces sélectionnées"


@admin.register(AdRating)
class AdRatingAdmin(admin.ModelAdmin):
    list_display = ('ad', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('ad__title', 'user__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)