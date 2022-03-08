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
    updateUser: List[types.UserType] = sb.django.mutations.update(types.UserUpdate, filters=types.UserFilter)


schema = sb.Schema(query=Query, mutation=Mutation)


"""
query A {
	user(pk: 1) {
    id
    firstName
  }
}

mutation M($id: ID!, $firstName: String) {
  updateUser(data: {id: $id, firstName: $firstName}) {
    id
    firstName
  }
}

{
  "id": 1,
  "firstName": "The Boss"
}
"""
