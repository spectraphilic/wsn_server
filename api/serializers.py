# Django
from django.utils import timezone
from rest_framework import serializers

# Project
from wsn.models import Metadata, Frame
from wsn.models import frame_to_database


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
        metadata, objs = frame_to_database(validated_data)
        return metadata

    # Override to_representation, otherwise the list of *all* frames attached
    # to the metadata will be returned
    def to_representation(self, instance):
        return {}


