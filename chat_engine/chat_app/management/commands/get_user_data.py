from django.core.management.base import BaseCommand
from chat_app.models import UserData 

class Command(BaseCommand):
    
    help = 'Get UserData by user_id'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=str, help='Add User Id')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        user_data = UserData.objects.filter(user_id=user_id)

        if not user_data.exists():
            self.stdout.write(self.style.WARNING('Not found records for user_id: {}'.format(user_id)))
            return

        for record in user_data:
            self.stdout.write(self.style.SUCCESS(str(record)))