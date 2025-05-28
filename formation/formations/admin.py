from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Sum
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta

from .models import FormationCategory, Formation, UserFormation, FormationReview


class EnrollmentCountFilter(SimpleListFilter):
    """Filtre personnalisé pour le nombre d'inscriptions"""
    title = _('Nombre d\'inscriptions')
    parameter_name = 'enrollment_count'

    def lookups(self, request, model_admin):
        return (
            ('0', _('Aucune inscription')),
            ('1-10', _('1-10 inscriptions')),
            ('11-50', _('11-50 inscriptions')),
            ('50+', _('Plus de 50 inscriptions')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(userformation__isnull=True)
        elif self.value() == '1-10':
            return queryset.annotate(
                enrollment_count=Count('userformation')
            ).filter(enrollment_count__gte=1, enrollment_count__lte=10)
        elif self.value() == '11-50':
            return queryset.annotate(
                enrollment_count=Count('userformation')
            ).filter(enrollment_count__gte=11, enrollment_count__lte=50)
        elif self.value() == '50+':
            return queryset.annotate(
                enrollment_count=Count('userformation')
            ).filter(enrollment_count__gt=50)


class RecentEnrollmentFilter(SimpleListFilter):
    """Filtre pour les inscriptions récentes"""
    title = _('Inscriptions récentes')
    parameter_name = 'recent_enrollment'

    def lookups(self, request, model_admin):
        return (
            ('today', _('Aujourd\'hui')),
            ('week', _('Cette semaine')),
            ('month', _('Ce mois')),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(date_enrolled__date=now.date())
        elif self.value() == 'week':
            week_ago = now - timedelta(days=7)
            return queryset.filter(date_enrolled__gte=week_ago)
        elif self.value() == 'month':
            month_ago = now - timedelta(days=30)
            return queryset.filter(date_enrolled__gte=month_ago)


@admin.register(FormationCategory)
class FormationCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'slug', 
        'formation_count_display', 
        'icon_display',
        'is_active',
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'formation_count_display')
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        (_('Paramètres'), {
            'fields': ('is_active',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formation_count_display(self, obj):
        """Affiche le nombre de formations dans la catégorie"""
        count = obj.formation_set.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:formations_formation_changelist')
            return format_html(
                '<a href="{}?category__id__exact={}">{} formation(s)</a>',
                url, obj.id, count
            )
        return "0 formation"
    formation_count_display.short_description = _('Formations')
    
    def icon_display(self, obj):
        """Affiche l'icône si disponible"""
        if obj.icon:
            return format_html('<i class="{}"></i> {}', obj.icon, obj.icon)
        return "-"
    icon_display.short_description = _('Icône')
    
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} catégorie(s) activée(s) avec succès.'
        )
    make_active.short_description = _('Activer les catégories sélectionnées')
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} catégorie(s) désactivée(s) avec succès.'
        )
    make_inactive.short_description = _('Désactiver les catégories sélectionnées')


class UserFormationInline(admin.TabularInline):
    """Inline pour voir les inscriptions dans le détail de la formation"""
    model = UserFormation
    extra = 0
    readonly_fields = ('date_enrolled', 'progress_percentage', 'completion_date')
    fields = (
        'user', 'payment_status', 'payment_method', 'amount_paid',
        'progress_percentage', 'completed', 'date_enrolled'
    )
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'price_display',
        'difficulty',
        'status',
        'enrollment_info',
        'rating_display',
        'thumbnail_display',
        'is_active',
        'is_featured'
    )
    list_filter = (
        'status',
        'difficulty',
        'is_active',
        'is_featured',
        'is_free',
        'category',
        EnrollmentCountFilter,
        'created_at'
    )
    search_fields = (
        'title', 
        'description', 
        'short_description',
        'meta_keywords',
        'slug'
    )
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'published_at',
        'enrollment_info',
        'rating_display',
        'completion_stats'
    )
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': (
                'title', 'slug', 'short_description', 'description',
                'category', 'thumbnail'
            )
        }),
        (_('Tarification'), {
            'fields': ('price', 'original_price', 'is_free'),
            'classes': ('collapse',)
        }),
        (_('Paramètres de formation'), {
            'fields': (
                'duration', 'difficulty', 'max_students',
                'prerequisites', 'learning_objectives'
            )
        }),
        (_('Contenu'), {
            'fields': ('video_url', 'pdf_content'),
            'classes': ('collapse',)
        }),
        (_('SEO et Marketing'), {
            'fields': (
                'meta_description', 'meta_keywords',
                'is_featured', 'status'
            ),
            'classes': ('collapse',)
        }),
        (_('Statistiques'), {
            'fields': ('enrollment_info', 'rating_display', 'completion_stats'),
            'classes': ('collapse',)
        }),
        (_('Paramètres système'), {
            'fields': ('is_active', 'created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [UserFormationInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category').annotate(
            enrollment_count=Count('userformation'),
            avg_rating=Avg('userformation__rating'),
            total_revenue=Sum('userformation__amount_paid')
        )
    
    def price_display(self, obj):
        """Affichage amélioré du prix"""
        if obj.is_free:
            return format_html('<span style="color: green; font-weight: bold;">GRATUIT</span>')
        
        price_html = f'{obj.price} CFA'
        if obj.original_price and obj.original_price > obj.price:
            price_html = format_html(
                '<span style="text-decoration: line-through; color: #999;">{} CFA</span><br>'
                '<span style="color: red; font-weight: bold;">{} CFA</span><br>'
                '<small style="color: green;">-{}%</small>',
                obj.original_price, obj.price, obj.discount_percentage
            )
        return format_html(price_html)
    price_display.short_description = _('Prix')
    
    def enrollment_info(self, obj):
        """Informations sur les inscriptions"""
        count = getattr(obj, 'enrollment_count', 0)
        revenue = getattr(obj, 'total_revenue', 0) or 0
        
        html = f'<strong>{count}</strong> inscription(s)<br>'
        if revenue > 0:
            html += f'<small>{revenue} CFA générés</small>'
        
        if obj.max_students:
            percentage = (count / obj.max_students) * 100
            color = 'red' if percentage > 80 else 'orange' if percentage > 60 else 'green'
            html += f'<br><span style="color: {color};">{percentage:.1f}% rempli</span>'
        
        return format_html(html)
    enrollment_info.short_description = _('Inscriptions')
    
    def rating_display(self, obj):
        """Affichage de la note moyenne"""
        avg_rating = getattr(obj, 'avg_rating', None)
        if avg_rating:
            stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
            return format_html(
                '{} <small>({:.1f}/5)</small>',
                stars, avg_rating
            )
        return "-"
    rating_display.short_description = _('Note')
    
    def thumbnail_display(self, obj):
        """Affichage de la miniature"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="50" height="30" style="object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail.url
            )
        return "-"
    thumbnail_display.short_description = _('Image')
    
    def completion_stats(self, obj):
        """Statistiques de complétion"""
        total = obj.userformation_set.filter(payment_status='COMPLETED').count()
        completed = obj.userformation_set.filter(completed=True).count()
        
        if total > 0:
            rate = (completed / total) * 100
            return format_html(
                '{}/{} complétées<br><small>{:.1f}% de réussite</small>',
                completed, total, rate
            )
        return "Aucune donnée"
    completion_stats.short_description = _('Taux de complétion')
    
    actions = [
        'make_active', 'make_inactive', 'make_featured', 
        'remove_featured', 'publish', 'make_draft'
    ]
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} formation(s) activée(s).')
    make_active.short_description = _('Activer les formations')
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} formation(s) désactivée(s).')
    make_inactive.short_description = _('Désactiver les formations')
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} formation(s) mise(s) en vedette.')
    make_featured.short_description = _('Mettre en vedette')
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} formation(s) retirée(s) de la vedette.')
    remove_featured.short_description = _('Retirer de la vedette')
    
    def publish(self, request, queryset):
        updated = queryset.update(status='PUBLISHED', published_at=timezone.now())
        self.message_user(request, f'{updated} formation(s) publiée(s).')
    publish.short_description = _('Publier les formations')
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='DRAFT')
        self.message_user(request, f'{updated} formation(s) mise(s) en brouillon.')
    make_draft.short_description = _('Mettre en brouillon')


@admin.register(UserFormation)
class UserFormationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'formation_link',
        'payment_status_display',
        'progress_display',
        'amount_paid',
        'date_enrolled',
        'completion_info'
    )
    list_filter = (
        'payment_status',
        'completed',
        'certificate_issued',
        RecentEnrollmentFilter,
        'formation__category',
        'payment_method'
    )
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'formation__title',
        'transaction_id'
    )
    readonly_fields = (
        'date_enrolled',
        'created_at',
        'updated_at',
        'completion_date'
    )
    
    fieldsets = (
        (_('Inscription'), {
            'fields': ('user', 'formation', 'date_enrolled')
        }),
        (_('Paiement'), {
            'fields': (
                'payment_status', 'payment_method',
                'transaction_id', 'amount_paid'
            )
        }),
        (_('Progression'), {
            'fields': (
                'progress_percentage', 'completed',
                'completion_date'
            )
        }),
        (_('Évaluation'), {
            'fields': ('rating', 'review', 'review_date'),
            'classes': ('collapse',)
        }),
        (_('Certificat'), {
            'fields': ('certificate_issued', 'certificate_url'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'formation', 'formation__category'
        )
    
    def formation_link(self, obj):
        """Lien vers la formation"""
        url = reverse('admin:formations_formation_change', args=[obj.formation.pk])
        return format_html('<a href="{}">{}</a>', url, obj.formation.title)
    formation_link.short_description = _('Formation')
    
    def payment_status_display(self, obj):
        """Affichage coloré du statut de paiement"""
        colors = {
            'PENDING': 'orange',
            'COMPLETED': 'green',
            'FAILED': 'red',
            'REFUNDED': 'purple'
        }
        color = colors.get(obj.payment_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_display.short_description = _('Statut paiement')
    
    def progress_display(self, obj):
        """Barre de progression visuelle"""
        percentage = obj.progress_percentage
        color = 'green' if percentage == 100 else 'orange' if percentage > 50 else 'red'
        
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; height: 20px; background: {}; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            percentage, color, percentage
        )
    progress_display.short_description = _('Progression')
    
    def completion_info(self, obj):
        """Informations de complétion"""
        if obj.completed:
            return format_html(
                '<span style="color: green;">✓ Terminé</span><br>'
                '<small>{}</small>',
                obj.completion_date.strftime('%d/%m/%Y') if obj.completion_date else 'Date inconnue'
            )
        elif obj.progress_percentage > 0:
            return format_html('<span style="color: orange;">En cours</span>')
        else:
            return format_html('<span style="color: red;">Non commencé</span>')
    completion_info.short_description = _('Complétion')
    
    actions = [
        'mark_as_completed', 'issue_certificates', 
        'mark_payment_completed', 'send_reminder_email'
    ]
    
    def mark_as_completed(self, request, queryset):
        for enrollment in queryset:
            enrollment.mark_as_completed()
        count = queryset.count()
        self.message_user(request, f'{count} formation(s) marquée(s) comme terminée(s).')
    mark_as_completed.short_description = _('Marquer comme terminé')
    
    def issue_certificates(self, request, queryset):
        updated = queryset.filter(completed=True).update(certificate_issued=True)
        self.message_user(request, f'{updated} certificat(s) émis.')
    issue_certificates.short_description = _('Émettre les certificats')
    
    def mark_payment_completed(self, request, queryset):
        updated = queryset.update(payment_status='COMPLETED')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme complété(s).')
    mark_payment_completed.short_description = _('Marquer paiement complété')


@admin.register(FormationReview)
class FormationReviewAdmin(admin.ModelAdmin):
    list_display = (
        'user_display',
        'formation_display',
        'rating_stars',
        'title',
        'is_verified',
        'is_approved',
        'helpful_count',
        'created_at'
    )
    list_filter = (
        'rating',
        'is_verified',
        'is_approved',
        'created_at',
        'user_formation__formation__category'
    )
    search_fields = (
        'user_formation__user__username',
        'user_formation__formation__title',
        'title',
        'content'
    )
    readonly_fields = ('created_at', 'updated_at', 'helpful_count')
    
    fieldsets = (
        (_('Avis'), {
            'fields': ('user_formation', 'rating', 'title', 'content')
        }),
        (_('Modération'), {
            'fields': ('is_verified', 'is_approved', 'helpful_count')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        return obj.user_formation.user.get_full_name() or obj.user_formation.user.username
    user_display.short_description = _('Utilisateur')
    
    def formation_display(self, obj):
        return obj.user_formation.formation.title
    formation_display.short_description = _('Formation')
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold;">{}</span>', stars)
    rating_stars.short_description = _('Note')
    
    actions = ['approve_reviews', 'unapprove_reviews', 'verify_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} avis approuvé(s).')
    approve_reviews.short_description = _('Approuver les avis')
    
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} avis désapprouvé(s).')
    unapprove_reviews.short_description = _('Désapprouver les avis')
    
    def verify_reviews(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} avis vérifié(s).')
    verify_reviews.short_description = _('Vérifier les avis')


# Configuration de l'admin principal
admin.site.site_header = _("Administration des Formations")
admin.site.site_title = _("Formations Admin")
admin.site.index_title = _("Gestion des Formations")

# Actions personnalisées au niveau du site
def export_selected_to_csv(modeladmin, request, queryset):
    """Action pour exporter les données sélectionnées en CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'
    
    writer = csv.writer(response)
    # Écrire les en-têtes et les données selon le modèle
    # Cette fonction peut être personnalisée selon les besoins
    
    return response

export_selected_to_csv.short_description = _("Exporter en CSV")