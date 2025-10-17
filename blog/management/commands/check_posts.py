from django.core.management.base import BaseCommand
from blog.models import Post
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check if there are any posts in the database'

    def handle(self, *args, **options):
        posts = Post.objects.all()
        count = posts.count()
        
        self.stdout.write(self.style.SUCCESS(f'Found {count} posts in the database'))
        
        if count > 0:
            self.stdout.write('\nFirst 5 posts:')
            for post in posts[:5]:
                self.stdout.write(f'- {post.title} (ID: {post.id}, Author: {post.author.username})')
        else:
            self.stdout.write('No posts found in the database. You may want to create some sample posts.')
            
            # Check if there are any users who could be authors
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.exists():
                self.stdout.write('\nAvailable users who could create posts:')
                for user in User.objects.all()[:5]:
                    self.stdout.write(f'- {user.username} (ID: {user.id})')
            else:
                self.stdout.write('\nNo users found in the database. You need to create a user first.')
