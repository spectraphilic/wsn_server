from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from . import api
from .utils import profile


query_profile = profile('/tmp/query.prof')

urlpatterns = [
    url(r'^api/create/$', api.CreateView.as_view()),
    url(r'^api/query/v2/$', api.Query2View.as_view()),
    # Include login URLs for the browsable API.
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

urlpatterns = format_suffix_patterns(urlpatterns)
