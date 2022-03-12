# Django
from django.contrib.auth.decorators import login_required
from django.urls import path

# GraphQL
from strawberry.django.views import GraphQLView

# Import from boot
from .schema import schema
from . import views


graphql = GraphQLView.as_view(schema=schema)

urlpatterns = [
    path('graphql/', login_required(graphql)),
    path('users/', views.UsersListView.as_view()),
    path('users/create/', views.UsersCreateView.as_view()),
    path('users/<id>/', views.UsersUpdateView.as_view()),
]
