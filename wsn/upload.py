# Standard Library
import csv
import datetime
import logging
import math

from wsn.models import Metadata, Frame


logger = logging.getLogger(__name__)


class Uploader:

    def upload(self, file):
        # Filename
        if type(file) is str:
            with open(file) as file:
                self.upload_file(file)
            return

        # Open file
        self.upload_file(file)

    def upload_file(self, file):
        raise NotImplementedError


class CR6Uploader(Uploader):

    def __convert(self, value, unit):
        if unit == 'TS':
            value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return value.replace(tzinfo=datetime.timezone.utc)

        if value == 'NAN':
            return math.nan

        try:
            return int(value)
        except ValueError:
            return float(value)

    def upload_file(self, file):
        reader = csv.reader(file)
        env = reader.__next__()
        assert len(env) == 8
        assert env[0] == 'TOA5'
        tags = {
            'name': env[1],                # mobileflux1
            'model': env[2],               # CR6
            'serial': int(env[3]),         # 744
            'os_version': env[4],          # CR6.Std.07
            'prog_name': env[5],           # CPU:flux_stations.CR6
            'prog_signature': int(env[6]), # 55208
            'table_name': env[7],          # Biomet
        }

        fields = reader.__next__()
        units = reader.__next__()
        reader.__next__() # abbreviations

        # Create Metadata
        metadata, created = Metadata.objects.get_or_create(tags=tags)

        # Frames
        for row in reader:
            data = {}
            for i, value in enumerate(row):
                name = fields[i]
                value = self.__convert(value, units[i])
                if name == 'TIMESTAMP':
                    time = value
                else:
                    data[name] = value

            Frame.update_or_create(metadata, time, data)
