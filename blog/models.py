import logging
import os
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from cloudinary_storage.storage import MediaCloudinaryStorage

logger = logging.getLogger(__name__)


class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def get_like_count(self):
        return self.likes.filter(is_like=True).count()
    
    def get_dislike_count(self):
        return self.likes.filter(is_like=False).count()
    
    def get_user_vote(self, user):
        if user.is_authenticated:
            try:
                like = self.likes.get(user=user)
                return like.is_like
            except:
                return None
        return None

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    is_like = models.BooleanField()  # True for like, False for dislike
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'post')  # One vote per user per post

    def __str__(self):
        vote_type = "liked" if self.is_like else "disliked"
        return f'{self.user.username} {vote_type} {self.post.title}'


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class Profile(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Public - Anyone can view my profile'),
        ('private', 'Private - Only I can view my profile'),
        ('registered', 'Registered Users - Only logged-in users can view my profile'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default-avatar.png')
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    website = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True, help_text='Your Twitter/X username (without @)')
    github_username = models.CharField(max_length=50, blank=True, help_text='Your GitHub username')
    facebook_url = models.URLField(blank=True, help_text='Your Facebook profile URL')
    instagram_username = models.CharField(max_length=50, blank=True, help_text='Your Instagram username (without @)')
    tiktok_username = models.CharField(max_length=50, blank=True, help_text='Your TikTok username (without @)')
    snapchat_username = models.CharField(max_length=50, blank=True, help_text='Your Snapchat username')
    linkedin_url = models.URLField(blank=True, help_text='Your LinkedIn profile URL')
    privacy_setting = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='public',
        help_text='Control who can view your profile'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def can_view_profile(self, requesting_user):
        """Check if the requesting user can view this profile"""
        if self.privacy_setting == 'public':
            return True
        if not requesting_user.is_authenticated:
            return False
        if self.privacy_setting == 'registered':
            return True
        if self.privacy_setting == 'private' and requesting_user == self.user:
            return True
        return False

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        try:
            # If this is an existing instance
            if self.pk:
                old_instance = Profile.objects.get(pk=self.pk)
                
                # Check if profile picture is being changed
                if old_instance.profile_picture and old_instance.profile_picture != self.profile_picture:
                    logger.info(f"Profile picture changed for user {self.user.username}")
                    logger.info(f"Old picture: {old_instance.profile_picture}")
                    logger.info(f"New picture: {self.profile_picture}")
                    
                    # Only delete if it's not the default avatar
                    if hasattr(old_instance.profile_picture, 'url') and 'default-avatar' not in old_instance.profile_picture.url:
                        try:
                            logger.info(f"Attempting to delete old profile picture: {old_instance.profile_picture}")
                            storage = old_instance.profile_picture.storage
                            storage.delete(old_instance.profile_picture.name)
                            logger.info("Successfully deleted old profile picture")
                        except Exception as e:
                            logger.error(f"Error deleting old profile picture: {str(e)}")
            
            # Save the instance
            super().save(*args, **kwargs)
            
            # If this is a new profile picture, log its details
            if self.profile_picture:
                logger.info(f"Profile picture saved successfully for {self.user.username}")
                if hasattr(self.profile_picture, 'url'):
                    logger.info(f"New picture URL: {self.profile_picture.url}")
                else:
                    logger.warning("Profile picture has no URL attribute")
                    
        except Exception as e:
            logger.error(f"Error in Profile.save(): {str(e)}", exc_info=True)
            raise

    def get_profile_picture_url(self):
        """
        Get the URL for the user's profile picture.
        Returns Cloudinary URL if available, otherwise returns the local URL or default.
        """
        try:
            # If no profile picture is set, return default
            if not self.profile_picture:
                return '/static/images/default-avatar.png'
                
            # Try to get Cloudinary URL if available
            if hasattr(self.profile_picture, 'url') and self.profile_picture.url:
                # If using Cloudinary, the URL will be a full URL
                if self.profile_picture.url.startswith(('http://', 'https://')):
                    return self.profile_picture.url
                # If it's a local path, prepend MEDIA_URL
                return f"{settings.MEDIA_URL}{self.profile_picture}"
                
            # Fallback to the file path
            if hasattr(self.profile_picture, 'path') and os.path.exists(self.profile_picture.path):
                return self.profile_picture.url
                
            # If we're here, the file might be missing but the reference exists
            logger.warning(f"Profile picture file missing for user {self.user.username}")
            return '/static/images/default-avatar.png'
            
        except Exception as e:
            logger.error(f"Error in get_profile_picture_url for user {getattr(self.user, 'username', 'unknown')}: {str(e)}")
            return '/static/images/default-avatar.png'
