from django.urls import include, path

from .api_create import CreateView
from .api_input import IridiumView, MeshliumView
from .api_query3 import QueryPostgreSQL, QueryClickHouse
from .api_upload import UploadEddyproView
from . import views


#from .utils import profile
#query_profile = profile('/tmp/query.prof')

urlpatterns = [
    # Bokeh
    path('explore/', views.explore),
    # API import data
    path('api/create/', CreateView.as_view()),
    path('api/upload/eddypro/', UploadEddyproView.as_view()),
    path('api/iridium/', IridiumView.as_view()),
    path('getpost_frame_parser.php', MeshliumView.as_view()),
    # API query: v3
    path('api/query/postgresql/', QueryPostgreSQL.as_view()),
    path('api/query/clickhouse/', QueryClickHouse.as_view()),
    # Include login URLs for the browsable API.
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
