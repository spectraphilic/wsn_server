from django.conf.urls import url, include
from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .api_4g import MeshliumView
from .api_create import CreateView
from .api_query import Query2View
from .api_upload import UploadEddyproView
from .utils import profile
from . import views


query_profile = profile('/tmp/query.prof')

urlpatterns = [
    # Include login URLs for the browsable API.
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # API
    url(r'^api/create/$', CreateView.as_view()),
    url(r'^api/query/v2/$', Query2View.as_view()),
    url(r'^api/upload/eddypro/$', UploadEddyproView.as_view()),
    url(r'^getpost_frame_parser.php$', MeshliumView.as_view()),
    # Bokeh
    path('explore/', views.explore),
]

urlpatterns = format_suffix_patterns(urlpatterns)
