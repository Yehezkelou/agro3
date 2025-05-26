# core/management/commands/cleanup_expired_ads.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from ads.models import Ad

class Command(BaseCommand):
    help = 'Nettoie les annonces expirées'

    def handle(self, *args, **options):
        expired_ads = Ad.objects.filter(expires_at__lt=timezone.now())
        count = expired_ads.count()
        expired_ads.delete()
        self.stdout.write(f'{count} annonces expirées supprimées.')