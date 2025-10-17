from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class CustomAdminSite(AdminSite):
    site_header = _('BlogWithMuhavi Administration')
    site_title = _('BlogWithMuhavi Admin')
    index_title = _('Welcome to BlogWithMuhavi Admin')
    
    def each_context(self, request):
        context = super().each_context(request)
        context['site_url'] = '/'
        
        # Add custom CSS class to body
        if 'bodyclass' not in context:
            context['bodyclass'] = ''
        context['bodyclass'] += ' custom-admin'
        
        # Add stats for the dashboard
        from blog.models import Post, Comment
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        context['stats'] = {
            'posts_count': Post.objects.count(),
            'comments_count': Comment.objects.count(),
            'users_count': User.objects.count(),
        }
        
        return context

# Create an instance of our custom admin site
admin_site = CustomAdminSite(name='admin')

# Call auto-registration
# auto_register_models()
