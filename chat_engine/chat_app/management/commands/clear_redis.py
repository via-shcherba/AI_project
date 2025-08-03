from django.core.management.base import BaseCommand
from chat_app.redis_client import clear_history

class Command(BaseCommand):
    help = 'Clear Redis history'

    def handle(self, *args, **options):
        clear_history()