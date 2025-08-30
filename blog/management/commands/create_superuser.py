from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a superuser automatically'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='griffinsmuhavi@gmail.com',
                password='janetsongole1964'
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully created superuser "admin" with email "griffinsmuhavi@gmail.com"')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Superuser "admin" already exists')
            )
