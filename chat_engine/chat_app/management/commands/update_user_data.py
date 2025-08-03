from django.core.management.base import BaseCommand
from chat_app.models import UserData


class Command(BaseCommand):
    
    help = 'Update UserData by user_id'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=str, help='Add User Id')
        parser.add_argument('field_name', type=str, help='Field Name')
        parser.add_argument('new_value', type=str, help='New Value')
        

    async def update_user_data(self, user_id, field_name, new_value):
        user_data = await UserData.objects.upsert(user_id=user_id, **{field_name: new_value})
        return user_data
    

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        field_name = kwargs['field_name']
        new_value = kwargs['new_value']
        
        import asyncio
        result = asyncio.run(self.update_user_data(user_id, field_name, new_value))
        if isinstance(result, Exception):
            self.stdout.write(self.style.WARNING(str(result)))
        else:
            self.stdout.write(self.style.SUCCESS('User Data updated successfully.'))