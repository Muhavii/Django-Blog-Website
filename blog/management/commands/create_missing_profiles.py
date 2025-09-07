from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Profile

class Command(BaseCommand):
    help = 'Create Profile for users who do not have one'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        count = 0
        for user in users_without_profiles:
            Profile.objects.create(user=user)
            count += 1
            self.stdout.write(self.style.SUCCESS(f'Created profile for {user.username}'))
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} profiles'))
