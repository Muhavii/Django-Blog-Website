from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, Http404
from django.views.static import serve
import os

def serve_media(request, path):
    """
    Custom media file serving for production
    """
    try:
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    except Http404:
        # Return a 404 response if file not found
        return HttpResponse(status=404)
