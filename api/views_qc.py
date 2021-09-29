# Rest framework
from rest_framework import generics, response
from django_filters import rest_framework as filters

# Project
from . import permissions
from . import serializers
from qc.models import Node, Data


class QCUploadView(generics.GenericAPIView):
    queryset = Node.objects.all()
    serializer_class = serializers.NodeListSerializer
    permission_classes = [
        permissions.with_api_key(lambda api_key: api_key.name == 'quality-control')
    ]

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)


class DataFilter(filters.FilterSet):
    time__gte = filters.NumberFilter(field_name='time', lookup_expr='gte')
    time__lt = filters.NumberFilter(field_name='time', lookup_expr='lt')

    class Meta:
        model = Data
        fields = ['time__gte', 'time__lt']


class QCDownloadView(generics.ListAPIView):
    serializer_class = serializers.DataSerializer
    permission_classes = [
        permissions.with_api_key(lambda api_key: api_key.name.startswith('quality-control'))
    ]

    # Filtering & pagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = DataFilter
    pagination_class = None

    def get_queryset(self):
        name = self.kwargs['name']
        return Data.objects.filter(node__name=name)
