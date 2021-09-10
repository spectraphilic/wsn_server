from rest_framework import generics, response
from rest_framework_api_key.permissions import HasAPIKey

from . import serializers
from qc.models import Node


class QCUploadView(generics.GenericAPIView):
    queryset = Node.objects.all()
    serializer_class = serializers.NodeListSerializer
    permission_classes = [HasAPIKey]

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)


class QCDownloadView(generics.ListAPIView):
    queryset = Node.objects.all()
    serializer_class = serializers.NodeSerializer
    permission_classes = [HasAPIKey]
