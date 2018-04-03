# Import from Django
from django.conf import settings
from django.core.files.storage import FileSystemStorage


sendfile_storage = FileSystemStorage(
    location=settings.SENDFILE_ROOT,
    base_url='/sendfile/',
)
