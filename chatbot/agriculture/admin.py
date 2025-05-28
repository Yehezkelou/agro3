from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import Culture, PratiqueAgricole

class PratiqueAgricoleInline(admin.TabularInline):
    model = PratiqueAgricole
    extra = 1
    fields = ('nom', 'saison', 'difficulte', 'date_creation')
    readonly_fields = ('date_creation', 'date_mise_a_jour')
    classes = ('collapse',)

@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_culture', 'cycle_croissance', 'image_preview', 'active')
    list_filter = ('type_culture', 'active')
    search_fields = ('nom', 'description')
    list_editable = ('active',)
    prepopulated_fields = {'slug': ('nom',)}
    inlines = (PratiqueAgricoleInline,)
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'slug', 'type_culture', 'description', 'active')
        }),
        ('Paramètres techniques', {
            'fields': ('cycle_croissance', 'besoin_eau', 'temperature_ideale'),
            'classes': ('collapse',)
        }),
        ('Image', {
            'fields': ('image', 'image_preview'),
        }),
    )
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Aperçu'

@admin.register(PratiqueAgricole)
class PratiqueAgricoleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'culture', 'saison', 'difficulte', 'date_creation')
    list_filter = ('saison', 'culture__type_culture', 'culture')
    search_fields = ('nom', 'description', 'avantages')
    date_hierarchy = 'date_creation'
    fieldsets = (
        ('Informations de base', {
            'fields': ('culture', 'nom', 'saison')
        }),
        ('Contenu', {
            'fields': ('description', 'avantages')
        }),
        ('Métriques', {
            'fields': ('difficulte',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_mise_a_jour'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('date_creation', 'date_mise_a_jour')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('culture')

# Personnalisation de l'interface admin
admin.site.site_header = "Administration Agrosmart"
admin.site.site_title = "Plateforme Agricole Intelligente"
admin.site.index_title = "Gestion des données agricoles"