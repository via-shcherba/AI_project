from django.core.management.base import BaseCommand
from chat_app.redis_client import redis_client 


class Command(BaseCommand):

    help = 'Clear translations from all user_data records in Redis'

    def handle(self, *args, **options):
        keys = redis_client.keys('user:*')
        fields = ['request_language', 'translation_dictionary']
        for field in fields:
            deleted_count = 0
            for key in keys:
                result = redis_client.hdel(key, field)
                if result == 1:
                    deleted_count += 1
                    self.stdout.write(f'Deleted field "{field}" from {key.decode() if isinstance(key, bytes) else key}')

            self.stdout.write(self.style.SUCCESS(
                f'Field "{field}" deleted from {deleted_count} user records.'
            ))