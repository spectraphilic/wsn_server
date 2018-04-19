# Django
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.functional import cached_property


# {'source_addr_long': '', 'rf_data': "", 'source_addr': '', 'id': '', 'options': ''}
# {"bat": 93, "serial": 408520806, "received": 1512673261, "humb": 41.20436096191406, "frame": 0, "tcb": 20.849998474121094, "pa": 101.06179809570312, "source_addr_long": 5526146534160749, "tst": 1512680400, "lw": 0.0, "in_temp": 21.25}

class Metadata(models.Model):
    tags = JSONField(default=dict, unique=True, editable=False)

    class Meta:
        indexes = [GinIndex(fields=['tags'])]

    def __str__(self):
        return str(self.tags)


class Frame(models.Model):
    time = models.DateTimeField(null=True, editable=False)
    data = JSONField(null=True, editable=False)
    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE,
                                 editable=False, related_name='frames',
                                 null=True)

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
#   bat 6238 int 87 100
#   frame 6238 int 0 255
    received = models.IntegerField(null=True, editable=False)
#   shf_cal(1) 174651 float 5.99847e-09 23.2295
#   shf_cal(2) 174651 float 2.603507e-09 22.06068
#   shf_cal_on_f 174651 int -1 0
#   sw12_1_state 174651 int -1 0
    TA_2_1_1_2_1 = models.FloatField(null=True, editable=False)
    RH_19_3_1_2_1 = models.FloatField(null=True, editable=False)
    TS_2_38_1_1_1 = models.FloatField(null=True, editable=False)
    TS_2_38_2_1_1 = models.FloatField(null=True, editable=False)
    TS_2_38_3_1_1 = models.FloatField(null=True, editable=False)
    SHF_6_37_1_1_1 = models.FloatField(null=True, editable=False)
    SHF_6_37_2_1_1 = models.FloatField(null=True, editable=False)
    TSS_2_99_1_1_1 = models.FloatField(null=True, editable=False)
    WD_20_35_1_1_1 = models.FloatField(null=True, editable=False)
    WS_16_33_1_1_1 = models.FloatField(null=True, editable=False)
    BEC_99_99_3_1_1 = models.FloatField(null=True, editable=False)
    SHF_99_37_1_1_2 = models.FloatField(null=True, editable=False)
    SHF_99_37_2_1_2 = models.FloatField(null=True, editable=False)
    SWC_12_36_3_1_1 = models.FloatField(null=True, editable=False)
    METNOR_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    METNOS_99_99_1_1_1 = models.FloatField(null=True, editable=False)
#   METNORA_99_99_1_1_1 233453 int 0 0
#   METNORR_99_99_1_1_1 233453 float 0 2.6
    FC1WSmax_16_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC1WSmin_16_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC2WSmax_16_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC2WSmin_16_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC1WSmean_16_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC2WSmean_16_99_1_1_1 = models.FloatField(null=True, editable=False)
    CS650PERIOD_99_99_3_1_1 = models.FloatField(null=True, editable=False)
    CS650VRATIO_99_99_3_1_1 = models.FloatField(null=True, editable=False)
    FC1DRIFTmax_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC1DRIFTmin_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC1DRIFTstd_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC1DRIFTsum_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC2DRIFTmax_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC2DRIFTmin_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC2DRIFTstd_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC2DRIFTsum_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC1DRIFTmean_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    FC2DRIFTmean_99_99_1_1_1 = models.FloatField(null=True, editable=False)
    PERMITTIVITY_99_99_3_1_1 = models.FloatField(null=True, editable=False)
#   LicorOn 292518 int 0 0
#   PowLicor 292518 int -1 -1
    CXTLA_tilt_X = models.FloatField(null=True, editable=False)
    CXTLA_tilt_Y = models.FloatField(null=True, editable=False)
#   P_RAIN_8_19_1_1_1 292518 float 0 0.2
    SURFACETEMP_2_99_1_1_1 = models.FloatField(null=True, editable=False)
#   SR50DISTANCE_9_99_1_1_1 292518 int -584 0
#   SR50QUALITY_99_99_1_1_1 292518 int 0 548
    T_nr = models.FloatField(null=True, editable=False)
    T_K_nr = models.FloatField(null=True, editable=False)
    batt_CR6 = models.FloatField(null=True, editable=False)
    Rl_up_meas = models.FloatField(null=True, editable=False)
#   buff_depth 467169 int 0 0
    panel_tmpr = models.FloatField(null=True, editable=False)
    Rl_down_meas = models.FloatField(null=True, editable=False)
#   process_time 467169 int 2857531 5000096
#   pulse_CNR4_Tot 467169 int 922 1257
    A116_panel_tmpr = models.FloatField(null=True, editable=False)
    FTPResult_Biomet = models.SmallIntegerField(null=True, editable=False)
    FTPResult_StationStatus = models.SmallIntegerField(null=True, editable=False)
    PA_4_2_1_1_1 = models.FloatField(null=True, editable=False)
    TA_2_1_1_1_1 = models.FloatField(null=True, editable=False)
    RH_19_3_1_1_1 = models.FloatField(null=True, editable=False)
    LWIN_6_14_1_1_1 = models.FloatField(null=True, editable=False)
    SWIN_6_10_1_1_1 = models.FloatField(null=True, editable=False)
    VIN_18_39_1_1_1 = models.FloatField(null=True, editable=False)
    LWOUT_6_15_1_1_1 = models.FloatField(null=True, editable=False)
    SWOUT_6_11_1_1_1 = models.FloatField(null=True, editable=False)
    RECORD = models.IntegerField(null=True, editable=False)

    class Meta:
        ordering = ['-time']
        unique_together = [('time', 'metadata')]

    @classmethod
    def get_data_fields(self):
        exclude = {'time', 'metadata', 'data'}
        return sorted([
            field.name for field in self._meta.fields
            if not field.editable and field.name not in exclude])

    @cached_property
    def address(self):
        if self.metadata is None:
            return None

        value = self.metadata.tags.get('source_addr_long')
        return ('%016X' % value) if value else None
