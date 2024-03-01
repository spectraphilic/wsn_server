# Django
from django.urls import path

# Import from boot
from .api import api
from . import views


urlpatterns = [
    path('api/', api.urls),
    path('users/', views.UsersListView.as_view()),
    path('users/create/', views.UsersCreateView.as_view()),
    path('users/<id>/', views.UsersUpdateView.as_view()),
]
