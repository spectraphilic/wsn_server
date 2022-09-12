# Django
from django.contrib.auth import get_user_model

# GraphQL
import strawberry as sb
from strawberry import auto


User = get_user_model()


@sb.django.filters.filter(User, lookups=True)
class UserFilter:
    id: auto

@sb.django.type(User)
class UserType:
    id: auto
    username: auto
    email: auto
    first_name: auto
    last_name: auto

@sb.django.input(User)
class UserCreate:
    username: auto
    email: auto
    first_name: auto
    last_name: auto

@sb.django.input(User, partial=True)
class UserUpdate:
    username: auto
    email: auto
    first_name: auto
    last_name: auto
