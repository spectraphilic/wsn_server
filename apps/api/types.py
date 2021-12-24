# Django
from django.contrib.auth import get_user_model

# GraphQL
import strawberry as sb
from strawberry.django import auto


User = get_user_model()


@sb.django.type(User)
class UserType:
    id: auto
    username: auto
    email: auto
    first_name: auto
    last_name: auto
