from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a superuser automatically or reset password if exists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='Reset password for existing admin user',
        )

    def handle(self, *args, **options):
        username = 'admin'
        email = 'griffinsmuhavi@gmail.com'
        password = 'janetsongole1964'
        
        try:
            user = User.objects.get(username=username)
            if options['reset_password']:
                user.set_password(password)
                user.email = email
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully reset password for superuser "{username}"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Superuser "{username}" already exists. Use --reset-password to reset.')
                )
        except User.DoesNotExist:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{username}" with email "{email}"')
            )
