# Import from Django
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible

@deconstructible
class SendfileStorage(FileSystemStorage):
    def __init__(self, **kwargs):
        kwargs['location'] = settings.SENDFILE_ROOT
        super(SendfileStorage, self).__init__(**kwargs)

sendfile_storage = SendfileStorage(base_url='/sendfile/')
