# Django
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import QueryDict
from django.shortcuts import render

# Project
from .models import ImportFile


@staff_member_required
def importfile_list(request):
    objects = ImportFile.objects.order_by('-updated_at', 'name', 'path')
    name = request.GET.get('name', '')
    if name:
        objects = objects.filter(name=name)
    status = request.GET.get('status', '')
    if status in ImportFile.Status.values:
        objects = objects.filter(status=status)

    # Filter and pager links must keep the active filters
    query = QueryDict(mutable=True)
    if name:
        query['name'] = name
    if status:
        query['status'] = status

    def querystring(**params):
        q = query.copy()
        for key, value in params.items():
            if value:
                q[key] = value
            else:
                q.pop(key, None)
        return f'?{q.urlencode()}'

    # Row counts per status, within the active name filter
    counts_qs = ImportFile.objects.all()
    if name:
        counts_qs = counts_qs.filter(name=name)
    status_counts = dict(
        counts_qs.values('status').annotate(count=Count('status')).values_list('status', 'count')
    )

    names = ImportFile.objects.values_list('name', flat=True).distinct().order_by('name')
    status_choices = [
        {'label': 'All', 'querystring': querystring(status=''), 'selected': not status,
         'count': sum(status_counts.values())},
    ] + [
        {'label': label, 'querystring': querystring(status=value),
         'selected': value == status, 'count': status_counts.get(value, 0)}
        for value, label in ImportFile.Status.choices
    ]
    name_choices = [
        {'label': 'All', 'querystring': querystring(name=''), 'selected': not name},
    ] + [
        {'label': value, 'querystring': querystring(name=value), 'selected': value == name}
        for value in names
    ]

    paginator = Paginator(objects, 100)
    page = paginator.get_page(request.GET.get('page'))
    page_range = paginator.get_elided_page_range(page.number)
    context = admin.site.each_context(request)
    context.update({
        'page': page,
        'page_range': page_range,
        'title': 'Import files',
        'status_choices': status_choices,
        'name_choices': name_choices,
        'query': query,
    })
    return render(request, 'wsn/importfile_list.html', context)
