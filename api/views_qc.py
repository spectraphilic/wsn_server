from rest_framework import generics, response

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


class QCDownloadView(generics.ListAPIView):
    serializer_class = serializers.DataSerializer
    pagination_class = None
    permission_classes = [
        permissions.with_api_key(lambda api_key: api_key.name.startswith('quality-control'))
    ]

    def get_queryset(self):
        name = self.kwargs['name']
        return Data.objects.filter(node__name=name)
