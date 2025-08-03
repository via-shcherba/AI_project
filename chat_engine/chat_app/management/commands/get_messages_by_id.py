import json
from django.core.management.base import BaseCommand
from chat_app.redis_client import redis_client

class Command(BaseCommand):

    help = 'Get messages by user_id'


    def add_arguments(self, parser):
        parser.add_argument('user_id', type=str, help='The ID of the user to fetch messages for')


    def handle(self, *args, **options):
        user_id = options['user_id']
        messages = self.get_messages_by_user_id(user_id)
        
        if messages:
            self.stdout.write(self.style.SUCCESS(f'Messages for user_id {user_id}:'))
            self.stdout.write('')
            for message in messages:
                self.stdout.write(f'- {message}')
                self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING(f'No messages found for user_id {user_id}.'))


    def get_messages_by_user_id(self, user_id):
        message_ids = redis_client.lrange(user_id, 0, -1) 
        messages = []
        for msg_id in message_ids:
            message = redis_client.hgetall(f'message:{msg_id}')
            if message.get('type') == 'file' and isinstance(message.get('response'), str):                
                message['response'] = json.loads(message['response'])               
            messages.append(message)
        return messages