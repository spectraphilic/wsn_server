from django.urls import path

# Project
from .api_create import CreateView
from .api_input import IridiumView, MeshliumView
from .api_query3 import QueryPostgreSQL, QueryClickHouse
from .api_upload import UploadEddyproView


#from wsn.utils import profile
#query_profile = profile('/tmp/query.prof')

urlpatterns = [
    # API import data
    path('api/create/', CreateView.as_view()),
    path('api/upload/eddypro/', UploadEddyproView.as_view()),
    path('api/iridium/', IridiumView.as_view()),
    path('getpost_frame_parser.php', MeshliumView.as_view()),
    # API query
    path('api/query/postgresql/', QueryPostgreSQL.as_view()),
    path('api/query/clickhouse/', QueryClickHouse.as_view()),
]
