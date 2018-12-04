from django.conf.urls import url, include
from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from . import api
from .utils import profile
from . import views


query_profile = profile('/tmp/query.prof')

urlpatterns = [
    url(r'^api/create/$', api.CreateView.as_view()),
    url(r'^api/query/v2/$', api.Query2View.as_view()),
    url(r'^getpost_frame_parser.php$', api.MeshliumView.as_view()),
    # Include login URLs for the browsable API.
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Bokeh
    path('explore/', views.explore),
]

urlpatterns = format_suffix_patterns(urlpatterns)
