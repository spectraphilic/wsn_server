import json

# Django
from django.conf import settings
from django.template import Library


register = Library()

def svelte_xxx(filename):
    # Local
    if settings.DEBUG and settings.INTERNAL_IPS:
        return f'http://localhost:5000/build/{filename}'

    # Server
    base = settings.STATIC_URL
    return base + f'build/{filename}'


@register.simple_tag
def svelte_js(name):
    path = f'{settings.BASE_DIR}/project/static/build/manifest.json'
    with open(path) as f:
        manifest = json.load(f)

    return svelte_xxx(manifest[f'{name}.js'])


@register.simple_tag
def svelte_css(name):
    return svelte_xxx(f'{name}.css')
