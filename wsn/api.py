# Standard Library
import base64
import logging

# Django
from django.db.models import F, Func, Min, Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# Rest framework
from rest_framework import generics
from rest_framework import pagination
from rest_framework import permissions
from rest_framework import serializers

# App
from .models import Metadata, Frame
from .parsers import waspmote


logger = logging.getLogger(__name__)


def frame_to_database(validated_data, update=True):
    tags = validated_data['tags']
    frames = validated_data['frames']
    metadata, created = Metadata.get_or_create(tags)
    for frame in frames:
        time = frame['time']
        data = frame['data']
        seq = data.pop('frame', None)
        Frame.create(metadata, time, seq, data, update=update)

    return metadata

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

    time = serializers.IntegerField()

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
        return frame_to_database(validated_data)

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
# Create frames sent through 4G by the waspmotes
#

@method_decorator(csrf_exempt, name='dispatch')
class MeshliumView(View):

    def post(self, request, *args, **kwargs):
        frames = request.POST.get('frame')
        if type(frames) is str:
            frames = [frames]

        for frame in frames:
            # Parse frame
            frame = base64.b16decode(frame)
            frame, _ = waspmote.parse_frame(frame)
            validated_data = waspmote.data_to_json(frame)

            # Add remote addr to tags
            remote_addr = request.META.get('REMOTE_ADDR', '')
            validated_data['tags']['remote_addr'] = remote_addr

            # Save to database
            frame_to_database(validated_data)

        return HttpResponse(status=200)

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
                if value is None and instance.data:
                    value = instance.data.get(field)
                if value is not None:
                    data[field] = value
        else:
            for field in instance.get_data_fields():
                value = getattr(instance, field, None)
                if value is not None:
                    data[field] = value
            if instance.data:
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


class Epoch(Func):
   function = 'EXTRACT'
   template = "%(function)s('epoch' from %(expressions)s)"


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
        exclude = {'format', 'limit', 'fields', 'tags', 'interval', 'time__gte', 'time__lte'}
        for key, value in params.items():
            if key not in exclude:
                if key.endswith(':int'):
                    key = key[:-4]
                    value = int(value)

                kw[key] = value

#       if not kw:
#           raise serializers.ValidationError('must narrow down the query')

        metadatas = Metadata.filter(**kw)
        metadatas = list(metadatas.values_list('id', flat=True))

        args, kw = [], {}

        # Frames
        queryset = Frame.objects.filter(metadata__in=metadatas)
        queryset = queryset.order_by('-time') # slow
        for key in 'time__gte', 'time__lte':
            value = params.get(key)
            if value is not None:
                kw[key] = int(value)

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

        # Interval
        interval = params.get('interval')
        if interval:
            subquery = queryset\
                .order_by()\
                .annotate(key=F('time') / int(interval))\
                .values('key')\
                .annotate(t=Min('time'))\
                .values('t')

            queryset = queryset.filter(time__in=subquery)

        tags = params.getlist('tags')
        return queryset.select_related('metadata') if tags else queryset
