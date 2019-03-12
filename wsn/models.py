# Standard Library
from datetime import datetime
import logging
import math

# Django
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db import transaction
from django.db.models import CASCADE, ForeignKey
from django.db.models import CharField
from django.db.models import FloatField # 8 bytes
from django.db.models import IntegerField # 4 bytes (signed)
#from django.db.models import PositiveIntegerField # 4 bytes (signed)
from django.db.models import SmallIntegerField # 2 bytes (signed)
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)

#
# XXX In theory we could (should) use this instead of 'double precision' in
# many fields. The CR6 program defines most fields as IEEE4, this should map
# to 'real' in PostgreSQL. But we find values such as 1.684204 in CR6 which
# loss precision when translated to Postgres. Try:
#
#   postgres=# select cast(1.684204 as real);
#
# It returns 1.6842 !
#

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
    tags = JSONField(null=True, editable=False)
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


class Frame(FlexModel):
    metadata = ForeignKey(Metadata, on_delete=CASCADE, related_name='frames',
                          null=True, editable=False)
    time = IntegerField(null=True, editable=False) # Unix epoch

    # Sequence number (motes)
    # Because the XBee frame is so small we have to split the logical frame,
    # these are merged back in the server.
    frame = SmallIntegerField(null=True, editable=False)
    frame_max = SmallIntegerField(null=True, editable=False)

    data = JSONField(null=True, editable=False)

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
    received = IntegerField(null=True, editable=False)

    # CR common
    RECORD = IntegerField(null=True, editable=False)

    # CR6 Status
    panel_tmpr = FloatField(null=True, editable=False) # IEEE4
    A116_panel_tmpr = FloatField(null=True, editable=False) # IEEE4
    batt_CR6 = FloatField(null=True, editable=False) # IEEE4
    process_time = IntegerField(null=True, editable=False) # IEEE4 microseconds
    buff_depth = IntegerField(null=True, editable=False) # IEEE4 scans
    # CR6 Status FTP_push
    FTPResult_Biomet = SmallIntegerField(null=True, editable=False) # FP2
    FTPResult_StationStatus = SmallIntegerField(null=True, editable=False) # FP2
    # CR6 Status Crydom_relay
    LicorOn = SmallIntegerField(null=True, editable=False) # FP2
    PowLicor = SmallIntegerField(null=True, editable=False) # FP2
    # CR6 Status Tilt
    CXTLA_tilt_X = FloatField(null=True, editable=False) # IEEE4
    CXTLA_tilt_Y = FloatField(null=True, editable=False) # IEEE4
    # CR6 Status TriStar
    # CR6 Status CNR_4
    T_nr = FloatField(null=True, editable=False) # IEEE4
    T_K_nr = FloatField(null=True, editable=False) # IEEE4
    Rl_down_meas = FloatField(null=True, editable=False) # IEEE4
    Rl_up_meas = FloatField(null=True, editable=False) # IEEE4
    pulse_CNR4_Tot = SmallIntegerField(null=True, editable=False) # FP2
    # CR6 Status HFP01SC
    shf_cal_1 = FloatField(null=True, editable=False) # IEEE4
    shf_cal_2 = FloatField(null=True, editable=False) # IEEE4
    shf_cal_on_f = SmallIntegerField(null=True, editable=False) # FP2
    sw12_1_state = SmallIntegerField(null=True, editable=False) # FP2

    # CR6 Biomet
    PA_4_2_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    VIN_18_39_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet HMP
    RH_19_3_1_2_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet MET (or EE_T)
    TA_2_1_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    TA_2_1_1_2_1 = FloatField(null=True, editable=False) # IEEE4
    TS_2_38_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    TSS_2_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    RH_19_3_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    WS_16_33_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    WD_20_35_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    METNORR_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    METNOR_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    METNORA_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    METNOS_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet NEDB
    P_RAIN_8_19_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet SR50A
    SR50DISTANCE_9_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    SR50QUALITY_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet CNR_4
    SWIN_6_10_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    SWOUT_6_11_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    LWIN_6_14_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    LWOUT_6_15_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet TCAV
    TS_2_38_2_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet SI411
    SURFACETEMP_2_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet CS650
    SWC_12_36_3_1_1 = FloatField(null=True, editable=False) # IEEE4
    BEC_99_99_3_1_1 = FloatField(null=True, editable=False) # IEEE4
    TS_2_38_3_1_1 = FloatField(null=True, editable=False) # IEEE4
    PERMITTIVITY_99_99_3_1_1 = FloatField(null=True, editable=False) # IEEE4
    CS650PERIOD_99_99_3_1_1 = FloatField(null=True, editable=False) # IEEE4
    CS650VRATIO_99_99_3_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet HFP01SC
    SHF_6_37_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    SHF_6_37_2_1_1 = FloatField(null=True, editable=False) # IEEE4
    SHF_99_37_1_1_2 = FloatField(null=True, editable=False) # IEEE4
    SHF_99_37_2_1_2 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet FlowCapt_1
    FC1DRIFTmin_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC1DRIFTmean_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC1DRIFTmax_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC1DRIFTstd_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC1DRIFTsum_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC1WSmin_16_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC1WSmean_16_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC1WSmax_16_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    # CR6 Biomet FlowCapt_2
    FC2DRIFTmin_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC2DRIFTmean_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC2DRIFTmax_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC2DRIFTstd_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC2DRIFTsum_99_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC2WSmin_16_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC2WSmean_16_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4
    FC2WSmax_16_99_1_1_1 = FloatField(null=True, editable=False) # IEEE4

    # Other
    TiltX_Avg = FloatField(null=True, editable=False)
    TiltY_Avg = FloatField(null=True, editable=False)
    RH1_19_3_1_1_1 = FloatField(null=True, editable=False)
    TA1_2_1_1_1 = FloatField(null=True, editable=False)


    class Meta:
        unique_together = [('metadata', 'time', 'frame')]

    json_field = 'data'
    non_data_fields = {'time', 'metadata', json_field, 'frame_max'}

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
            except Exception as ex:
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
    for frame in frames:
        time = frame['time']
        data = frame['data']
        seq = data.pop('frame', None)
        Frame.create(metadata, time, seq, data, update=update)

    return metadata
