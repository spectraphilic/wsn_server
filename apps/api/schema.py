# Standard Library
from typing import List

# GraphQL
import strawberry as sb

# Project
from . import types


@sb.type
class Query:
    users: List[types.UserType] = sb.django.field()


schema = sb.Schema(query=Query)
