from rest_framework import generics, response

from . import permissions, serializers
from qc.models import Node


class QCUploadView(generics.GenericAPIView):
    queryset = Node.objects.all()
    serializer_class = serializers.NodeListSerializer
    permission_classes = [permissions.CreatePermission]

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)
