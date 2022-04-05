# Django
from django.contrib.auth.decorators import login_required
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

# Project
from .views_qc import QCUploadView, QCDownloadView
from .views_wsn import CreateView, IridiumView, MeshliumView
from .views_wsn import QueryPostgreSQL, QueryClickHouse
from .views_wsn import UploadEddyproView


app_name = 'api'

urlpatterns = [
    # wsn: import data
    path('api/create/', CreateView.as_view()),
    path('api/upload/eddypro/', UploadEddyproView.as_view()),
    path('api/iridium/', IridiumView.as_view()),
    path('getpost_frame_parser.php', MeshliumView.as_view()),
    # wsn: query
    path('api/query/postgresql/', QueryPostgreSQL.as_view()),
    path('api/query/clickhouse/', QueryClickHouse.as_view()),
    # Quality Control
    path('api/qc/upload/', QCUploadView.as_view(), name='qc-upload'),
    path('api/qc/download/<name>/', QCDownloadView.as_view(), name='qc-download'),
    # Schema & docs
    path('api/schema/', login_required(SpectacularAPIView.as_view()), name='schema'),
    path('api/', login_required(SpectacularRedocView.as_view(url_name='api:schema')), name='redoc'),
]
