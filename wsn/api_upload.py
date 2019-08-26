# Standard Library
import io
import json

# Django
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# Rest framework
from rest_framework.response import Response
from rest_framework.views import APIView

# App
from .api_create import CreatePermission
from .parsers.eddypro import EddyproParser
from .upload import upload2pg, archive


@method_decorator(csrf_exempt, name='dispatch')
class UploadEddyproView(APIView):
    permission_classes = (CreatePermission,)

    def post(self, request, *args, **kw):
        # Read metadata
        metadata = json.loads(request.data['metadata'].read())
        assert metadata.get('name')

        # Read data file
        data = request.data['data']
        filename = data.name
        data = data.read()

        parser = EddyproParser()
        metadata, fields, rows = parser.parse(
            io.StringIO(data.decode('utf-8')),
            metadata=metadata,
        )

        # Import to database
        metadata = upload2pg(None, metadata, fields, rows)

        # Archive, keep a copy of the source file in the filesystem
        archive(metadata.name, filename, data)

        # Ok
        return Response(status=201)
