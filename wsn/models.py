# Standard Library
from datetime import datetime
import logging
import math
from time import time as epoch_float

# Django
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db import transaction
from django.db.models import ForeignKey, PROTECT
from django.db.models import CharField
from django.db.models import FloatField # 8 bytes
from django.db.models import IntegerField # 4 bytes (signed)
#from django.db.models import PositiveIntegerField # 4 bytes (signed)
from django.db.models import SmallIntegerField # 2 bytes (signed)
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

# Project
from .utils import TimeModelMixin


logger = logging.getLogger(__name__)


# The CR6 program defines most fields as IEEE4, actually the CR6 doesn't
# support double precision. However in the CSV file we find values such as
# 1.684204, 146.4748 or 202.6803; these values cannot be represented exactly
# with simple precision floats. So we've 2 choices:
#
# 1. We can use double precision to store the number exactly as we find it into
#    the CSV file.
# 2. We can use simple precision, since the source data is single precision,
#    the value in the CSV file must be wrong anyway.
#
# Many command line tools, such as the clickhouse and postgres clients, round
# the printed numbers, so the information displayed may be misleading:
#
#     postgres=# select cast(1.684204 as real), cast(cast(1.684204 as real) as double precision);
#     float4 |      float8
#    --------+------------------
#     1.6842 | 1.68420398235321
#    (1 row)

class Float4Field(FloatField):
    description = _("Floating point number (4 bytes)")
    def db_type(self, connection):
        return 'real'


class FlexQuerySet(models.QuerySet):
    def extract_from_json(self, fields=None, dryrun=True):
        for obj in self:
            obj.extract_from_json(fields, dryrun)


class FlexModel(models.Model):
    """
    Abstract model.
    """

    class Meta:
        abstract = True

    objects = FlexQuerySet.as_manager()

    # Override in subclasses
    json_field = None
    non_data_fields = {}

    @classmethod
    def get_data_fields(self):
        """
        Return the sorted list of data fields.
        """
        exclude = self.non_data_fields
        return sorted([
            field.name for field in self._meta.fields
            if not field.editable and field.name not in exclude])

    @classmethod
    def normalize_name(self, name):
        """
        Some names are not valid Python identifiers, so we replace the
        offending chars. For examle 'shf_cal(1)' will become 'shf_cal_1_'
        """
        trans = str.maketrans('()', '__')
        return name.translate(trans).rstrip('_')

    def get_value(self, name):
        value = getattr(self, name, None)
        if value is None:
            data = getattr(self, self.json_field)
            return data.get(value)

        return value

    def extract_from_json(self, fields=None, dryrun=True):
        if fields is None:
            fields = set(self.get_data_fields())

        data = getattr(self, self.json_field)
        new_values = {}

        changed = False
        for src in list(data):
            dst = self.normalize_name(src)
            if dst in fields:
                changed = True
                value = data.pop(src)
                if value is not None:
                    if value == "NAN": # FIXME Only if target field is float
                        value = math.nan
                    new_values[dst] = value
                    setattr(self, dst, value)

        if data == {}:
            setattr(self, self.json_field, None)
            changed = True

        if changed:
            if dryrun:
                print(f'{data} {new_values}')
            else:
                self.save()

        return changed


class Metadata(FlexModel):
    tags = models.JSONField(null=True, editable=False)
    name = CharField(max_length=255, null=True, editable=False)

    class Meta:
        indexes = [GinIndex(fields=['tags'])]
        unique_together = [('name', 'tags')]

    def __str__(self):
        return f'{self.name} {self.tags}'

    json_field = 'tags'
    non_data_fields = {json_field}

    @classmethod
    def get_or_create(self, tags):
        name = tags.pop('name', None)
        return Metadata.objects.get_or_create(name=name, tags=tags)

    @classmethod
    def filter(self, **kw):
        fields = set(self.get_data_fields())

        search = {}
        for name, value in kw.items():
            if name in fields:
                search[name] = value
            else:
                search[f'tags__{name}'] = value

        return self.objects.filter(**search)


def epoch():
    return round(epoch_float())

class Frame(TimeModelMixin, FlexModel):

    metadata = ForeignKey(Metadata, on_delete=PROTECT, related_name='frames',
                          null=True, editable=False)

    # Time (unix epoch)
    time = IntegerField(null=True, editable=False) # Sample time
    received = IntegerField(null=True, editable=False) # Gateway time
    inserted = IntegerField(null=True, editable=False, default=epoch)

    # Sequence number (motes)
    # Because the XBee frame is so small we have to split the logical frame,
    # these are merged back in the server.
    frame = SmallIntegerField(null=True, editable=False)
    frame_max = SmallIntegerField(null=True, editable=False)

    data = models.JSONField(null=True, editable=False)

    # Extracted from .data to save memory space
#   mb_sd 573 int 0 31
#   mb_median 573 int 1439 1955
#   rssi 622 int -92 -65
#   ds2_dir 2057 float 0.0 356.0
#   ds2_gust 2057 float 0.0 35.540000915527344
#   ds2_temp 2057 float -18.5 0.6000000238418579
#   ds2_speed 2057 float 0.0 34.709999084472656
#   ds2_zonal 2057 float -13.25 23.889999389648438
#   ds2_meridional 2057 float -26.579999923706055 6.849999904632568
#   ds1820 4153 <class 'list'> None None
    bat = SmallIntegerField(null=True, editable=False)

    # CR common
    RECORD = IntegerField(null=True, editable=False)

    # Other
    TiltX_Avg = FloatField(null=True, editable=False)
    TiltY_Avg = FloatField(null=True, editable=False)

    class Meta:
        unique_together = [('metadata', 'time', 'frame')]

    json_field = 'data'
    non_data_fields = {'metadata', 'time', 'inserted', json_field, 'frame_max'}

    @classmethod
    def create(self, metadata, time, seq, data, update=False):
        """
        Create a new frame:

        - If update is True and there's already a row with the given metadata
          and time, then update the row.

        - If update is False (default) and there's already a row with the given
          metadata and time, then skip the row.

        Data fields which do not have a column in the database are stored in
        the 'data' column, of json datatype.
        """
        if type(time) is datetime:
            if time.tzinfo is None:
                raise ValueError('unexpected naive datetime, expected integer (epoch) or aware datetime')
            time = int(time.timestamp())

        if time > (2**31 - 1):
            logger.warning(
                f'Discarding frame with unexpected time={time} from metadata={metadata.id}'
            )
            return None, False

        defaults = {
            name: data.pop(name) for name in self.get_data_fields()
            if name in data}

        # The JSON datatype does not support NAN values, so we replace them by
        # the 'NAN' string
        for key, value in data.items():
            if value is math.nan:
                data[key] = 'NAN'

        if data:
            defaults['data'] = data

        kw = {
            'metadata': metadata, 'time': time, 'frame': seq, # Unique
            'defaults': defaults, # Data
        }

        if update:
            obj, created = self.objects.update_or_create(**kw)
            msg = 'Row updated pk=%s'
        else:
            obj, created = self.objects.get_or_create(**kw)
            msg = 'Row skipped pk=%s'

        if not created:
            logger.warning(msg, obj.pk)

        # Merge
        if created and seq is not None:
            try:
                self.merge_frames(metadata, time, save=True)
            except Exception:
                logger.exception(f'failed to merge frames metadata={metadata.id} time={time}')

        return obj, created


    @classmethod
    def merge_frames(self, metadata, time, save=False, debug=None):
        frames = self.objects.filter(metadata=metadata, time=time)

        # TODO Instead of ordering by received, order by frame, in a smart way
        # because the frame sequence wraps (0, .., 255, 0, ..)
        # Then we will support:
        # - parsing old unordered frames
        # - parsing frames from the SD card (they don't have received)
        frames = frames.order_by('received')

        first = None
        for frame in frames:
            if debug is not None:
                debug(frame)

            if first is None:
                first = frame
            else:
                first.merge_frame(frame, save=save)

        return first

    def merge_frame(self, frame, save=False):
        # Merge only if same metadata and time
        assert self.metadata is not None and self.time is not None
        assert frame.metadata_id == self.metadata_id
        assert frame.time == self.time

        # Support merging frames comming from motes via Pi
        assert self.frame is not None and self.received is not None
        assert frame.frame is not None and frame.received is not None

        # Only consecutive frames
        frame_max = self.frame_max if self.frame_max is not None else self.frame
        assert (frame_max + 1) % 256 == frame.frame
        self.frame_max = frame.frame

        # Data fields
        ignore = {'frame', 'received'}
        for name in self.get_data_fields():
            first_value = getattr(self, name)
            value = getattr(frame, name)
            if value is None or name in ignore:
                pass
            elif type(first_value) is list and type(value) is list:
                raise NotImplementedError(f'{name} is a list')
            elif first_value is None:
                setattr(self, name, value)
            elif first_value != value:
                assert first_value is None, f'field={name} duped'

        # JSON
        for name in frame.data:
            first_value = self.data.get(name)
            value = frame.data.get(name)
            if value is None:
                pass
            elif type(first_value) is list and type(value) is list:
                self.data[name].extend(value) # The case of DS18B20 and similar
            elif first_value is None:
                self.data[name] = value
            elif first_value != value:
                assert first_value is None, f'field=data.{name} duped'

        if save:
            with transaction.atomic():
                self.save()
                frame.delete()


    @cached_property
    def address(self):
        if self.metadata is None:
            return None

        value = self.metadata.tags.get('source_addr_long')
        return ('%016X' % value) if value else None


def frame_to_database(validated_data, update=False):
    tags = validated_data['tags']
    frames = validated_data['frames']
    metadata, created = Metadata.get_or_create(tags)

    objs = []
    for frame in frames:
        time = frame['time']
        data = frame['data']
        seq = data.pop('frame', None)
        obj, created = Frame.create(metadata, time, seq, data, update=update)
        if obj is not None:
            objs.append(obj)

    return metadata, objs
