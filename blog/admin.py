from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from myproject.admin_site import admin_site
from .models import Post, Comment, Like, Profile

# Import the custom admin site
from myproject.admin_site import admin_site as custom_admin_site

class ImagePreviewMixin:
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 200px; max-width: 200px; object-fit: contain;" />')
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin, ImagePreviewMixin):
    list_display = ['title', 'author', 'created_at', 'view_count', 'image_preview']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at', 'view_count', 'image_preview']
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'author')
        }),
        ('Media', {
            'fields': ('image', 'image_preview')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'view_count'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if 'image' in form.changed_data and obj.image:
            # Handle image resizing here if needed
            pass
        super().save_model(request, obj, form, change)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content']

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'is_like', 'created_at']
    list_filter = ['is_like', 'created_at']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin, ImagePreviewMixin):
    list_display = ['user', 'location', 'created_at', 'profile_picture_preview']
    list_filter = ['created_at', 'location']
    search_fields = ['user__username', 'bio', 'location']
    readonly_fields = ['created_at', 'updated_at', 'profile_picture_preview']
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return mark_safe(f'<img src="{obj.profile_picture.url}" style="max-height: 200px; max-width: 200px; border-radius: 50%; object-fit: cover;" />')
        return "No Profile Picture"
    profile_picture_preview.short_description = 'Profile Picture Preview'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'bio', 'location', 'birth_date')
        }),
        ('Social Media', {
            'fields': ('website', 'twitter_handle', 'github_username', 'facebook_url', 
                      'instagram_username', 'tiktok_username', 'snapchat_username', 'linkedin_url'),
            'classes': ('collapse',)
        }),
        ('Profile Picture', {
            'fields': ('profile_picture', 'profile_picture_preview')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'privacy_setting'),
            'classes': ('collapse',)
        }),
    )
