from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin import AdminSite
from django.apps import apps

class CustomAdminSite(AdminSite):
    site_header = 'Muhavi\'s Blog Administration'
    site_title = 'Muhavi\'s Blog Admin'
    index_title = 'Welcome to Muhavi\'s Blog Admin'
    
    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        # Get the original app list
        app_dict = self._build_app_dict(request)
        app_list = list(app_dict.values())

        # Sort the apps and models
        app_list.sort(key=lambda x: x['name'].lower())
        
        for app in app_list:
            if 'models' in app:
                app['models'].sort(key=lambda x: x['name'].lower())
        
        return app_list

    def each_context(self, request):
        """
        Add custom context variables for the admin interface.
        """
        context = super().each_context(request)
        context['site_url'] = '/'
        return context

# Create an instance of our custom admin site
admin_site = CustomAdminSite(name='custom_admin')

# Register default admin classes
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin

# Unregister any previously registered models
admin_site._registry = {}

# Register default models
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)

# Auto-register all models from installed apps
def auto_register_models():
    from django.apps import apps
    from django.contrib import admin
    
    for model in apps.get_models():
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass

# Call auto-registration
# auto_register_models()
