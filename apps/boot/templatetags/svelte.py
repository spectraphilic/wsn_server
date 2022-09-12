# Django
from django.template import Library

# Requirements
from django_vite.templatetags.django_vite import DjangoViteAssetLoader


register = Library()

@register.inclusion_tag('boot/vite_mount.html')
def vite_mount(path, name, props, target):
    url = DjangoViteAssetLoader.instance().generate_vite_asset_url(path)
    return {
        'url': url,
        'name': name,
        'props': props,
        'target': target,
        'data_name': f'{name}-data',
    }
