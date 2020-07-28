import json

# Django
from django.conf import settings
from django.template import Library


register = Library()

@register.simple_tag
def svelte_js():
    path = f'{settings.BASE_DIR}/project/static/build/manifest.json'
    with open(path) as f:
        manifest = json.load(f)

    filename = manifest['main.js']

    # Local
    if settings.DEBUG and settings.INTERNAL_IPS:
        return f'http://localhost:5000/build/{filename}'

    # Server
    base = settings.STATIC_URL
    return base + f'build/{filename}'
