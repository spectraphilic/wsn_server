# Django
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import QueryDict
from django.shortcuts import render

# Project
from .models import ImportFile


@staff_member_required
def importfile_list(request):
    objects = ImportFile.objects.all()
    name = request.GET.get('name', '')
    if name:
        objects = objects.filter(name=name)
    status = request.GET.get('status', '')
    if status in ImportFile.Status.values:
        objects = objects.filter(status=status)

    # Pager links must keep the active filters
    query = QueryDict(mutable=True)
    if name:
        query['name'] = name
    if status:
        query['status'] = status

    names = ImportFile.objects.values_list('name', flat=True).distinct().order_by('name')
    paginator = Paginator(objects, 100)
    page = paginator.get_page(request.GET.get('page'))
    context = admin.site.each_context(request)
    context.update({
        'page': page,
        'title': 'Import files',
        'names': names,
        'statuses': ImportFile.Status.choices,
        'name': name,
        'status': status,
        'query': query,
    })
    return render(request, 'wsn/importfile_list.html', context)
