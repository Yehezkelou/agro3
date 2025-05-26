from django.contrib import admin
from .models import Category, Advertisement, AdvertisementImage, Favorite


class AdvertisementImageInline(admin.TabularInline):
    model = AdvertisementImage
    extra = 1
    fields = ('image', 'caption', 'is_main')
    readonly_fields = ('get_image_preview',)
    
    def get_image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />'
        return "Pas d'image"
    get_image_preview.short_description = "Aperçu"
    get_image_preview.allow_tags = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_ads_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def get_ads_count(self, obj):
        return obj.advertisements.count()
    get_ads_count.short_description = "Nombre d'annonces"


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'category', 'status', 'created_at', 'is_premium')
    list_filter = ('status', 'category', 'is_premium', 'created_at')
    search_fields = ('title', 'description', 'author__username', 'author__email')
    raw_id_fields = ('author',)
    date_hierarchy = 'created_at'
    inlines = [AdvertisementImageInline]
    readonly_fields = ('created_at', 'updated_at', 'slug')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'description', 'author')
        }),
        ('Détails', {
            'fields': ('category', 'price', 'status', 'is_premium')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_published', 'make_draft', 'make_premium']
    
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} annonces ont été publiées.')
    make_published.short_description = "Marquer comme publié"
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} annonces ont été mises en brouillon.')
    make_draft.short_description = "Marquer comme brouillon"
    
    def make_premium(self, request, queryset):
        updated = queryset.update(is_premium=True)
        self.message_user(request, f'{updated} annonces ont été marquées premium.')
    make_premium.short_description = "Marquer comme premium"


@admin.register(AdvertisementImage)
class AdvertisementImageAdmin(admin.ModelAdmin):
    list_display = ('get_image_preview', 'advertisement', 'caption', 'is_main', 'get_file_size')
    list_filter = ('is_main',)
    raw_id_fields = ('advertisement',)
    search_fields = ('advertisement__title', 'caption')
    readonly_fields = ('get_image_preview', 'get_file_size')
    
    def get_image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />'
        return "Pas d'image"
    get_image_preview.short_description = "Aperçu"
    get_image_preview.allow_tags = True
    
    def get_file_size(self, obj):
        if obj.image:
            size = obj.image.size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024*1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        return "N/A"
    get_file_size.short_description = "Taille du fichier"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'advertisement', 'created_at')
    list_filter = ('created_at',)
    raw_id_fields = ('user', 'advertisement')
    search_fields = ('user__username', 'advertisement__title')
    date_hierarchy = 'created_at'
    
    def has_change_permission(self, request, obj=None):
        # Les favoris ne peuvent généralement pas être modifiés
        return False


# Configuration globale de l'admin
admin.site.site_header = "Administration des Publicités"
admin.site.site_title = "Admin Publicités"
admin.site.index_title = "Gestion des annonces"


# Classe alternative si vous voulez une vue plus simple
class SimpleAdvertisementAdmin(admin.ModelAdmin):
    """Version simplifiée de l'admin pour Advertisement"""
    list_display = ('title', 'author', 'price', 'status', 'created_at')
    list_filter = ('status', 'is_premium')
    search_fields = ('title', 'author__username')
    
    # Décommentez pour utiliser cette version à la place
    # admin.site.unregister(Advertisement)
    # admin.site.register(Advertisement, SimpleAdvertisementAdmin)