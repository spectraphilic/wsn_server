from django.urls import path

# Project
from .views_wsn import CreateView, IridiumView, MeshliumView
from .views_wsn import QueryPostgreSQL, QueryClickHouse
from .views_wsn import UploadEddyproView


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
