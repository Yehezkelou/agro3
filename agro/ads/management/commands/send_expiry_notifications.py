from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ...models import Ad
from ...utils import send_ad_notification


class Command(BaseCommand):
    help = 'Envoie des notifications pour les annonces qui expirent bientôt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Nombre de jours avant expiration pour notifier'
        )

    def handle(self, *args, **options):
        days = options['days']
        expiry_date = timezone.now() + timedelta(days=days)
        
        expiring_ads = Ad.objects.filter(
            status='approved',
            campaign_end__lte=expiry_date,
            campaign_end__gt=timezone.now()
        )
        
        sent_count = 0
        for ad in expiring_ads:
            if send_ad_notification(ad, 'expiring'):
                sent_count += 1
                self.stdout.write(
                    f'Notification envoyée pour l\'annonce: {ad.title}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{sent_count} notification(s) d\'expiration envoyée(s)'
            )
        )