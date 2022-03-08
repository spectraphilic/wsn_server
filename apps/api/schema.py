# Standard Library
from typing import List

# GraphQL
import strawberry as sb

# Project
from . import types


@sb.type
class Query:
    users: List[types.UserType] = sb.django.field()
    user: types.UserType = sb.django.field()


@sb.type
class Mutation:
    createUser: List[types.UserType] = sb.django.mutations.create(types.UserCreate)
    updateUser: List[types.UserType] = sb.django.mutations.update(types.UserUpdate, filters=types.UserFilter)


schema = sb.Schema(query=Query, mutation=Mutation)
