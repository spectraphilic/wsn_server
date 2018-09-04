from wsn.models import Metadata, Frame
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.licor import LicorParser


class CR6Uploader:

    def upload(self, filepath):
        with CR6Parser(filepath) as parser:
            # Create Metadata
            metadata, created = Metadata.objects.get_or_create(tags=parser.tags)
            # Frames
            for time, data in parser:
                Frame.create(metadata, time, data)


class LicorUploader:

    def upload(self, filepath):
        # Do not upload biomet frames, as these are just a copy of the CR6
        # frames (1 of 12 actually)

        with LicorParser(filepath) as parser:
            # Data frames
            datafile = parser.data
            metadata, created = Metadata.objects.get_or_create(tags=datafile.header)
            for time, data in datafile:
                Frame.create(metadata, time, data)
