from chat_app.redis_client import redis_client
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    
    
    help = 'Retrieve or delete user history from Redis by user_id'
    
    
    def add_arguments(self, parser):
        parser.add_argument('user_id', type=str, help='User ID to fetch or delete history')
        parser.add_argument('--delete', action='store_true', help='Delete history for user_id')
        

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        
        if kwargs['delete']:
            self.delete_history(user_id)
        else:
            self.retrieve_history(user_id)
            

    def retrieve_history(self, user_id):
        history = redis_client.lrange(user_id, 0, -1)
        if not history:
            self.stdout.write(self.style.WARNING(f'No history found for user_id: {user_id}'))
            return
        self.stdout.write(self.style.SUCCESS(f'Chat History for user_id: {user_id}:'))
        for record in history:
            self.stdout.write(self.style.SUCCESS(str(record)))
            

    def delete_history(self, user_id):
        result = redis_client.delete(user_id)
        if result == 0:
            self.stdout.write(self.style.WARNING(f'No history found to delete for user_id: {user_id}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted history for user_id: {user_id}'))