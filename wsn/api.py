# Standard Library
import datetime
import logging

# Django
from django.db.models import Q
from django.utils import timezone

# Rest framework
from rest_framework import generics
from rest_framework import pagination
from rest_framework import permissions
from rest_framework import serializers

# App
from .models import Metadata, Frame


logger = logging.getLogger(__name__)


# https://stackoverflow.com/questions/22881067/django-rest-framework-post-array-of-objects
class ManyModelMixin(object):
    def get_serializer(self, *args, **kwargs):
        if 'many' not in kwargs:
            data = kwargs.get('data')
            if type(data) is list:
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)


#
# Create
#

class DateTimeField(serializers.DateTimeField):
    default_error_messages = {
        'naive': 'Datetime value is missing a timezone.'
    }

    def enforce_timezone(self, value):
        if timezone.is_naive(value):
            self.fail('naive')
        return super().enforce_timezone(value)


class FrameSerializer(serializers.ModelSerializer):

    time = DateTimeField()

    class Meta:
        model = Frame
        fields = ['time', 'data']
        extra_kwargs = {
            'time': {'read_only': False},
            'data': {'read_only': False},
        }


class MetadataSerializer(serializers.ModelSerializer):
    frames = FrameSerializer(many=True)

    class Meta:
        model = Metadata
        fields = ['tags', 'frames']
        extra_kwargs = {'tags': {'read_only': False}}

    def create(self, validated_data):
        frames_data = validated_data.pop('frames')
        metadata, created = Metadata.objects.get_or_create(**validated_data)
        for frame_data in frames_data:
            time = frame_data['time']
            data = frame_data['data']
            Frame.update_or_create(metadata, time, data)

        return metadata

    # Override to_representation, otherwise the list of *all* frames attached
    # to the metadata will be returned
    def to_representation(self, instance):
        return {}


class CreatePermission(permissions.BasePermission):
    """
    Only the special user "api" is allowed to create frames.
    """

    def has_permission(self, request, view):
        user = request.user
        return user and user.username == 'api'


class CreateView(generics.CreateAPIView):
    queryset = Metadata.objects.all()
    serializer_class = MetadataSerializer
    permission_classes = (CreatePermission,)

#
# Query v2
#
class Query2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Frame
        fields = ['time']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        params = self.context['request'].query_params

        # Fields
        fields = params.getlist('fields')
        if fields:
            for field in fields:
                value = getattr(instance, field, None)
                if value is None:
                    value = instance.data.get(field)
                if value is not None:
                    data[field] = value
        else:
            for field in instance.get_data_fields():
                value = getattr(instance, field, None)
                if value is not None:
                    data[field] = value
            data.update(instance.data)

        # Tags
        tags = params.getlist('tags')
        if tags:
            metadata = instance.metadata
            for tag in tags:
                value = metadata.tags.get(tag)
                if value is not None:
                    data[tag] = value

        return data


class Query2Pagination(pagination.CursorPagination):
    ordering = ['time']
    page_size_query_param = 'limit'


class Query2View(generics.ListAPIView):
    serializer_class = Query2Serializer
    permission_classes = (permissions.IsAuthenticated,)
    #permission_classes = (permissions.AllowAny,)
    pagination_class = Query2Pagination

    def get_queryset(self):
        params = self.request.query_params

        # Metadatas
        # TODO Optimize using data__contains when key does not end by __gte/__lte
        # because __contains will trigger usage of the GIN index.
        kw = {}
        exclude = {'format', 'limit', 'fields', 'tags', 'time__gte', 'time__lte'}
        for key, value in params.items():
            if key not in exclude:
                if key.endswith(':int'):
                    key = key[:-4]
                    value = int(value)

                kw['tags__{}'.format(key)] = value

#       if not kw:
#           raise serializers.ValidationError('must narrow down the query')

        metadatas = Metadata.objects.filter(**kw)
        metadatas = list(metadatas.values_list('id', flat=True))

        args, kw = [], {}

        # Frames
        queryset = Frame.objects.filter(metadata__in=metadatas)
        queryset = queryset.order_by('-time') # slow
        for key in 'time__gte', 'time__lte':
            value = params.get(key)
            if value is not None:
                value = datetime.datetime.utcfromtimestamp(float(value))
                kw[key] = value.replace(tzinfo=datetime.timezone.utc)

        # Fields
        fields = params.getlist('fields')
        if fields:
            if len(fields) == 1:
                q = Q(data__has_key=fields[0])
            else:
                q = Q(data__has_any_keys=fields)

            # Fields defined in the schema
            for field in set(fields) & set(Frame.get_data_fields()):
                q |= Q(**{'%s__isnull' % field: False})

            args.append(q)

        queryset = queryset.filter(*args, **kw)

        tags = params.getlist('tags')
        return queryset.select_related('metadata') if tags else queryset
