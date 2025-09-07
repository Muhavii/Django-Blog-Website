"""
Test script to verify admin URLs are properly configured.
Run with: python test_admin_urls.py
"""
import os
import sys
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.urls import get_resolver

def print_urls(urls=None, prefix=''):
    if urls is None:
        urls = get_resolver().url_patterns
    
    for pattern in urls:
        if hasattr(pattern, 'url_patterns'):
            print_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            print(f"{prefix}{pattern.pattern} -> {pattern.name or 'No name'}")

if __name__ == '__main__':
    print("Admin URLs:")
    admin_urls = [p for p in get_resolver().url_patterns 
                 if hasattr(p, 'namespace') and p.namespace == 'admin']
    print_urls(admin_urls[0].url_patterns if admin_urls else [])
