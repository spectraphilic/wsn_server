# Django
from django.utils import timezone

# Rest framework
from rest_framework import generics
from rest_framework import permissions
from rest_framework import serializers

# App
from .models import Metadata, Frame
from .models import frame_to_database


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
