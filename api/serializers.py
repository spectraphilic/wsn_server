# Django
from django.utils import timezone
from rest_framework import fields, serializers

# Project
from qc.models import Node, Data
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


#
# Quality control
#

class DataSerializer(serializers.ModelSerializer):

    class Meta:
        model = Data
        fields = [
            'time', 'temperature', 'temperature_qc', 'humidity', 'humidity_qc',
            'air_pressure', 'air_pressure_qc', 'snow_depth', 'snow_depth_qc']
        extra_kwargs = {key: {'read_only': False} for key in fields}


class NodeSerializer(serializers.ModelSerializer):

    data = DataSerializer(many=True)

    class Meta:
        model = Node
        fields = ['name', 'data']

    def run_validation(self, data=fields.empty):
        # This makes validation to work when updating
        queryset = self.parent.instance
        name = data['name']
        self.instance = queryset.filter(name=name).first()

        return super().run_validation(data=data)

    def create_or_update(self, validated_data):
        name = validated_data.pop('name')
        data = validated_data.pop('data')

        node, created = Node.objects.get_or_create(name=name)
        for data in data:
            time = data.pop('time')
            Data.objects.get_or_create(node=node, time=time, **data)

        return node


class NodeListSerializer(serializers.ListSerializer):

    child = NodeSerializer()

    def update(self, queryset, validated_data):
        return [
            self.child.create_or_update(attrs) for attrs in validated_data
        ]
