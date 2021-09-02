from rest_framework import generics
from . import permissions, serializers
from qc.models import Node


class QCUploadView(generics.CreateAPIView):
    queryset = Node.objects.all()
    serializer_class = serializers.NodeSerializer
    permission_classes = [permissions.CreatePermission]
