from django.core.management.base import BaseCommand
from django.utils import timezone
from ...models import Ad
from ...utils import send_ad_notification


class Command(BaseCommand):
    help = 'Met à jour le statut des annonces expirées'

    def handle(self, *args, **options):
        expired_ads = Ad.objects.filter(
            status='approved',
            campaign_end__lt=timezone.now()
        )
        
        count = 0
        for ad in expired_ads:
            ad.status = 'expired'
            ad.save()
            count += 1
            
            # Optionnel: envoyer une notification d'expiration
            # send_ad_notification(ad, 'expired')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{count} annonce(s) marquée(s) comme expirée(s)'
            )
        )