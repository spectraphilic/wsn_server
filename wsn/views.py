# Django
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render

# Project
from .models import ImportFile


@staff_member_required
def importfile_list(request):
    paginator = Paginator(ImportFile.objects.all(), 100)
    page = paginator.get_page(request.GET.get('page'))
    context = admin.site.each_context(request)
    context.update({'page': page, 'title': 'Import files'})
    return render(request, 'wsn/importfile_list.html', context)
