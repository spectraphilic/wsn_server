from wsn.models import Metadata, Frame
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.licor import LicorParser


class CR6Uploader:

    def upload(self, file):
        with CR6Parser(file) as parser:
            # Create Metadata
            metadata, created = Metadata.objects.get_or_create(tags=parser.tags)
            # Frames
            for time, data in parser:
                Frame.update_or_create(metadata, time, data)


class LicorUploader:

    def upload(self, file):
        with LicorParser(file) as parser:
            # Data frames
            datafile = parser.data
            metadata, created = Metadata.objects.get_or_create(tags=datafile.header)
            for time, data in datafile:
                Frame.update_or_create(metadata, time, data)

            # Biomet frames
            datafile = parser.biomet_data
            metadata, created = Metadata.objects.get_or_create(tags=datafile.header)
            for time, data in datafile:
                Frame.update_or_create(metadata, time, data)
