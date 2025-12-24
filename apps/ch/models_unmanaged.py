# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from clickhouse_backend import models


class FinseSommer(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    supply_voltage = models.Float64Field(db_column='Supply voltage')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cube_dir_value = models.Float64Field(db_column='Cube, Dir.value')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exception_code = models.Float64Field(db_column='Exception code')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    relay_b = models.Float64Field(db_column='Relay B')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    heating_current = models.Float64Field(db_column='Heating current')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rod_temperature = models.Float64Field(db_column='Rod, Temperature')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rod_ice = models.Float64Field(db_column='Rod, Ice')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    relais_a_counte = models.Float64Field(db_column='Relais A, counte')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    humidity = models.Float64Field(db_column='Humidity')  # Field name made lowercase.
    cube_temperatur = models.Float64Field(db_column='Cube, Temperatur')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    temperature = models.Float64Field(db_column='Temperature')  # Field name made lowercase.
    cube_ice = models.Float64Field(db_column='Cube, Ice')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    relay_function = models.Float64Field(db_column='Relay function')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rod_water = models.Float64Field(db_column='Rod, Water')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    relais_b_counte = models.Float64Field(db_column='Relais B, counte')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cube_ice_rate = models.Float64Field(db_column='Cube, Ice rate')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cube_direction = models.Float64Field(db_column='Cube, Direction')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    relais_b_time = models.Float64Field(db_column='Relais B, time')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cube_water = models.Float64Field(db_column='Cube, Water')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    relay_a = models.Float64Field(db_column='Relay A')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dew_point = models.Float64Field(db_column='Dew point')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    relais_a_time = models.Float64Field(db_column='Relais A, time')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rod_direction = models.Float64Field(db_column='Rod, Direction')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rod_ice_rate = models.Float64Field(db_column='Rod, Ice rate')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rod_dir_value = models.Float64Field(db_column='Rod, Dir.value')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    mrl_7_supply = models.Float64Field(db_column='MRL-7 Supply')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    modem_csq = models.Float64Field(db_column='Modem CSQ')  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'finse_sommer'


class FinsefluxBiomet(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    wd_20_35_1_1_1 = models.Float64Field(db_column='WD_20_35_1_1_1')  # Field name made lowercase.
    fc1wsmax_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmax_16_99_1_1_1')  # Field name made lowercase.
    fc2driftsum_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTsum_99_99_1_1_1')  # Field name made lowercase.
    fc2driftmean_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmean_99_99_1_1_1')  # Field name made lowercase.
    cs650vratio_99_99_3_1_1 = models.Float64Field(db_column='CS650VRATIO_99_99_3_1_1')  # Field name made lowercase.
    fc1wsmin_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmin_16_99_1_1_1')  # Field name made lowercase.
    lwin_6_14_1_1_1 = models.Float64Field(db_column='LWIN_6_14_1_1_1')  # Field name made lowercase.
    fc1driftmax_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmax_99_99_1_1_1')  # Field name made lowercase.
    swin_6_10_1_1_1 = models.Float64Field(db_column='SWIN_6_10_1_1_1')  # Field name made lowercase.
    shf_6_37_2_1_1 = models.Float64Field(db_column='SHF_6_37_2_1_1')  # Field name made lowercase.
    ta_2_1_1_2_1 = models.Float64Field(db_column='TA_2_1_1_2_1')  # Field name made lowercase.
    metnora_99_99_1_1_1 = models.Float64Field(db_column='METNORA_99_99_1_1_1')  # Field name made lowercase.
    shf_99_37_2_1_1 = models.Float64Field(db_column='SHF_99_37_2_1_1')  # Field name made lowercase.
    metnorr_99_99_1_1_1 = models.Float64Field(db_column='METNORR_99_99_1_1_1')  # Field name made lowercase.
    ts_2_38_2_1_1 = models.Float64Field(db_column='TS_2_38_2_1_1')  # Field name made lowercase.
    bec_99_99_3_1_1 = models.Float64Field(db_column='BEC_99_99_3_1_1')  # Field name made lowercase.
    vin_18_39_1_1_1 = models.Float64Field(db_column='VIN_18_39_1_1_1')  # Field name made lowercase.
    shf_99_37_1_1_1 = models.Float64Field(db_column='SHF_99_37_1_1_1')  # Field name made lowercase.
    swout_6_11_1_1_1 = models.Float64Field(db_column='SWOUT_6_11_1_1_1')  # Field name made lowercase.
    fc1driftmin_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmin_99_99_1_1_1')  # Field name made lowercase.
    tss_2_99_1_1_1 = models.Float64Field(db_column='TSS_2_99_1_1_1')  # Field name made lowercase.
    fc1driftmean_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmean_99_99_1_1_1')  # Field name made lowercase.
    ts_2_38_3_1_1 = models.Float64Field(db_column='TS_2_38_3_1_1')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    ts_2_38_1_1_1 = models.Float64Field(db_column='TS_2_38_1_1_1')  # Field name made lowercase.
    fc2driftmin_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmin_99_99_1_1_1')  # Field name made lowercase.
    ta_2_1_1_1_1 = models.Float64Field(db_column='TA_2_1_1_1_1')  # Field name made lowercase.
    rh_19_3_1_2_1 = models.Float64Field(db_column='RH_19_3_1_2_1')  # Field name made lowercase.
    fc2driftmax_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmax_99_99_1_1_1')  # Field name made lowercase.
    metnor_99_99_1_1_1 = models.Float64Field(db_column='METNOR_99_99_1_1_1')  # Field name made lowercase.
    lwout_6_15_1_1_1 = models.Float64Field(db_column='LWOUT_6_15_1_1_1')  # Field name made lowercase.
    fc1driftstd_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTstd_99_99_1_1_1')  # Field name made lowercase.
    rh_19_3_1_1_1 = models.Float64Field(db_column='RH_19_3_1_1_1')  # Field name made lowercase.
    fc1driftsum_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTsum_99_99_1_1_1')  # Field name made lowercase.
    fc1wsmean_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmean_16_99_1_1_1')  # Field name made lowercase.
    fc2wsmin_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmin_16_99_1_1_1')  # Field name made lowercase.
    fc2wsmax_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmax_16_99_1_1_1')  # Field name made lowercase.
    shf_6_37_1_1_1 = models.Float64Field(db_column='SHF_6_37_1_1_1')  # Field name made lowercase.
    fc2driftstd_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTstd_99_99_1_1_1')  # Field name made lowercase.
    ws_16_33_1_1_1 = models.Float64Field(db_column='WS_16_33_1_1_1')  # Field name made lowercase.
    fc2wsmean_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmean_16_99_1_1_1')  # Field name made lowercase.
    pa_4_2_1_1_1 = models.Float64Field(db_column='PA_4_2_1_1_1')  # Field name made lowercase.
    swc_12_36_3_1_1 = models.Float64Field(db_column='SWC_12_36_3_1_1')  # Field name made lowercase.
    cs650period_99_99_3_1_1 = models.Float64Field(db_column='CS650PERIOD_99_99_3_1_1')  # Field name made lowercase.
    permittivity_99_99_3_1_1 = models.Float64Field(db_column='PERMITTIVITY_99_99_3_1_1')  # Field name made lowercase.
    metnos_99_99_1_1_1 = models.Float64Field(db_column='METNOS_99_99_1_1_1')  # Field name made lowercase.
    shf_99_37_2_1_2 = models.Float64Field(db_column='SHF_99_37_2_1_2')  # Field name made lowercase.
    shf_99_37_1_1_2 = models.Float64Field(db_column='SHF_99_37_1_1_2')  # Field name made lowercase.
    tot_precip_part = models.Float64Field()
    dc9 = models.Float64Field()
    drizzle_part = models.Float64Field()
    dc8 = models.Float64Field()
    dc2 = models.Float64Field()
    dc7 = models.Float64Field()
    precip_type_d = models.Float64Field(db_column='precip_type_D')  # Field name made lowercase.
    dc5 = models.Float64Field()
    dc1 = models.Float64Field()
    precip_abs_d = models.Float64Field(db_column='precip_abs_D')  # Field name made lowercase.
    dc11 = models.Float64Field()
    precip_int_h_d = models.Float64Field(db_column='precip_int_h_D')  # Field name made lowercase.
    dc3 = models.Float64Field()
    tot_drops = models.Float64Field()
    dc6 = models.Float64Field()
    precip_diff_d = models.Float64Field(db_column='precip_diff_D')  # Field name made lowercase.
    dc10 = models.Float64Field()
    dc0 = models.Float64Field()
    snow_part = models.Float64Field()
    dc4 = models.Float64Field()
    precip_int_min_d = models.Float64Field(db_column='precip_int_min_D')  # Field name made lowercase.
    hail_part = models.Float64Field()
    metnorr_010_99_99_1_1_1 = models.Float64Field(db_column='METNORR_010_99_99_1_1_1')  # Field name made lowercase.
    metnoma_01_99_99_1_1_1 = models.Float64Field(db_column='METNOmA_01_99_99_1_1_1')  # Field name made lowercase.
    pa_4_2_2_1_1 = models.Float64Field(db_column='PA_4_2_2_1_1')  # Field name made lowercase.
    metnorr_011_99_99_1_1_1 = models.Float64Field(db_column='METNORR_011_99_99_1_1_1')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'finseflux_Biomet'


class FinsefluxHfdata(models.ClickhouseModel):
    timestamp = models.DateTime64Field(db_column='TIMESTAMP', precision=3, primary_key=True)  # Field name made lowercase.
    co2 = models.Float64Field(db_column='CO2')  # Field name made lowercase.
    t_in = models.Float64Field(db_column='T_in')  # Field name made lowercase.
    ux = models.Float64Field(db_column='Ux')  # Field name made lowercase.
    uy = models.Float64Field(db_column='Uy')  # Field name made lowercase.
    uz = models.Float64Field(db_column='Uz')  # Field name made lowercase.
    h2o = models.Float64Field(db_column='H2O')  # Field name made lowercase.
    ptotal = models.Float64Field(db_column='Ptotal')  # Field name made lowercase.
    sos_ana = models.Float64Field(db_column='SOS_ana')  # Field name made lowercase.
    sonic_diag = models.Float64Field()
    w_ana = models.Float64Field(db_column='W_ana')  # Field name made lowercase.
    u_ana = models.Float64Field(db_column='U_ana')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    v_ana = models.Float64Field(db_column='V_ana')  # Field name made lowercase.
    t_out = models.Float64Field(db_column='T_out')  # Field name made lowercase.
    co2_dry = models.Float64Field(db_column='CO2_dry')  # Field name made lowercase.
    sos = models.Float64Field(db_column='SOS')  # Field name made lowercase.
    h2o_dry = models.Float64Field(db_column='H2O_dry')  # Field name made lowercase.
    agc = models.Float64Field(db_column='AGC')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'finseflux_HFData'


class FinsefluxStationstatus(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    pulse_cnr4_tot = models.Float64Field(db_column='pulse_CNR4_Tot')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    t_nr = models.Float64Field(db_column='T_nr')  # Field name made lowercase.
    shf_cal_on_f = models.Float64Field()
    buff_depth = models.Float64Field()
    panel_tmpr = models.Float64Field()
    shf_cal_1_field = models.Float64Field(db_column='shf_cal(1)')  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    rl_down_meas = models.Float64Field(db_column='Rl_down_meas')  # Field name made lowercase.
    sw12_1_state = models.Float64Field()
    ftpresult_biomet = models.Float64Field(db_column='FTPResult_Biomet')  # Field name made lowercase.
    t_k_nr = models.Float64Field(db_column='T_K_nr')  # Field name made lowercase.
    shf_cal_2_field = models.Float64Field(db_column='shf_cal(2)')  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    rl_up_meas = models.Float64Field(db_column='Rl_up_meas')  # Field name made lowercase.
    batt_cr6 = models.Float64Field(db_column='batt_CR6')  # Field name made lowercase.
    process_time = models.Float64Field()
    ftpresult_stationstatus = models.Float64Field(db_column='FTPResult_StationStatus')  # Field name made lowercase.
    a116_panel_tmpr = models.Float64Field(db_column='A116_panel_tmpr')  # Field name made lowercase.
    a116_panel_tmpr4 = models.Float64Field(db_column='A116_panel_tmpr4')  # Field name made lowercase.
    a116_panel_tmpr1 = models.Float64Field(db_column='A116_panel_tmpr1')  # Field name made lowercase.
    a116_panel_tmpr3 = models.Float64Field(db_column='A116_panel_tmpr3')  # Field name made lowercase.
    a116_panel_tmpr2 = models.Float64Field(db_column='A116_panel_tmpr2')  # Field name made lowercase.
    skipped_scans = models.Float64Field()
    crdresult_stationstatus = models.Float64Field(db_column='CRDResult_StationStatus')  # Field name made lowercase.
    crdresult_biomet = models.Float64Field(db_column='CRDResult_BIOMET')  # Field name made lowercase.
    a116_panel_tmpr_1_field = models.Float64Field(db_column='A116_panel_tmpr(1)')  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    a116_panel_tmpr_2_field = models.Float64Field(db_column='A116_panel_tmpr(2)')  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    a116_panel_tmpr_4_field = models.Float64Field(db_column='A116_panel_tmpr(4)')  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    timeoffset = models.Float64Field(db_column='TimeOffset')  # Field name made lowercase.
    a116_panel_tmpr_3_field = models.Float64Field(db_column='A116_panel_tmpr(3)')  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    crdresult_hfdata = models.Float64Field(db_column='CRDResult_HFData')  # Field name made lowercase.
    ftpresult_hfdata = models.Float64Field(db_column='FTPResult_HFData')  # Field name made lowercase.
    buffdepth = models.Float64Field(db_column='BuffDepth')  # Field name made lowercase.
    slowproctime2 = models.Float64Field(db_column='SlowProcTime2')  # Field name made lowercase.
    skippedslowscan2 = models.Float64Field(db_column='SkippedSlowScan2')  # Field name made lowercase.
    skippedscan = models.Float64Field(db_column='SkippedScan')  # Field name made lowercase.
    processtime = models.Float64Field(db_column='ProcessTime')  # Field name made lowercase.
    skippedslowscan1 = models.Float64Field(db_column='SkippedSlowScan1')  # Field name made lowercase.
    maxproctime = models.Float64Field(db_column='MaxProcTime')  # Field name made lowercase.
    slowproctime1 = models.Float64Field(db_column='SlowProcTime1')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'finseflux_StationStatus'


class GruvebadetData(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    atmos22_dir = models.Float64Field(db_column='ATMOS22_DIR')  # Field name made lowercase.
    fc2driftmean_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmean_99_99_1_1_1')  # Field name made lowercase.
    atmos22_tc = models.Float64Field(db_column='ATMOS22_TC')  # Field name made lowercase.
    skipped_scans = models.Float64Field()
    fc2wsmean_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmean_16_99_1_1_1')  # Field name made lowercase.
    atmos22_east_ws = models.Float64Field(db_column='ATMOS22_East_WS')  # Field name made lowercase.
    atmos22_gust = models.Float64Field(db_column='ATMOS22_Gust')  # Field name made lowercase.
    fc1wsmin_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmin_16_99_1_1_1')  # Field name made lowercase.
    ftpresult_diagnostic = models.Float64Field(db_column='FTPResult_Diagnostic')  # Field name made lowercase.
    fc1driftsum_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTsum_99_99_1_1_1')  # Field name made lowercase.
    batt_cr6 = models.Float64Field(db_column='batt_CR6')  # Field name made lowercase.
    atmos22_compassheading = models.Float64Field(db_column='ATMOS22_compassHeading')  # Field name made lowercase.
    fc1wsmean_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmean_16_99_1_1_1')  # Field name made lowercase.
    fc1driftmin_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmin_99_99_1_1_1')  # Field name made lowercase.
    fc1driftmax_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmax_99_99_1_1_1')  # Field name made lowercase.
    atmos22_north_ws = models.Float64Field(db_column='ATMOS22_North_WS')  # Field name made lowercase.
    fc2driftsum_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTsum_99_99_1_1_1')  # Field name made lowercase.
    crdresult_diagnostic = models.Float64Field(db_column='CRDResult_Diagnostic')  # Field name made lowercase.
    atmos22_x_ori = models.Float64Field(db_column='ATMOS22_X_Ori')  # Field name made lowercase.
    fc2driftstd_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTstd_99_99_1_1_1')  # Field name made lowercase.
    fc1driftmean_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmean_99_99_1_1_1')  # Field name made lowercase.
    fc2wsmin_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmin_16_99_1_1_1')  # Field name made lowercase.
    ftpresult_data = models.Float64Field(db_column='FTPResult_Data')  # Field name made lowercase.
    fc2driftmin_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmin_99_99_1_1_1')  # Field name made lowercase.
    crdresult_data = models.Float64Field(db_column='CRDResult_Data')  # Field name made lowercase.
    fc2driftmax_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmax_99_99_1_1_1')  # Field name made lowercase.
    atmos22_y_ori = models.Float64Field(db_column='ATMOS22_Y_Ori')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    process_time = models.Float64Field()
    buff_depth = models.Float64Field()
    panel_tmpr_cr6 = models.Float64Field(db_column='panel_tmpr_CR6')  # Field name made lowercase.
    fc1wsmax_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmax_16_99_1_1_1')  # Field name made lowercase.
    fc2wsmax_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmax_16_99_1_1_1')  # Field name made lowercase.
    atmos22_ws = models.Float64Field(db_column='ATMOS22_WS')  # Field name made lowercase.
    fc1driftstd_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTstd_99_99_1_1_1')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'gruvebadet_Data'


class GruvebadetDiagnostic(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    skippedsystemscan = models.Float64Field(db_column='SkippedSystemScan')  # Field name made lowercase.
    paneltemp_max = models.Float64Field(db_column='PanelTemp_Max')  # Field name made lowercase.
    battery_max = models.Float64Field(db_column='Battery_Max')  # Field name made lowercase.
    starttime = models.DateTime64Field(db_column='StartTime', precision=3)  # Field name made lowercase.
    pakbusaddress = models.Float64Field(db_column='PakBusAddress')  # Field name made lowercase.
    progname = models.StringField(db_column='ProgName')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    paneltemp_min = models.Float64Field(db_column='PanelTemp_Min')  # Field name made lowercase.
    low12vcount = models.Float64Field(db_column='Low12VCount')  # Field name made lowercase.
    lithiumbattery = models.Float64Field(db_column='LithiumBattery')  # Field name made lowercase.
    osversion = models.StringField(db_column='OSVersion')  # Field name made lowercase.
    compileresults = models.StringField(db_column='CompileResults')  # Field name made lowercase.
    progsignature = models.Float64Field(db_column='ProgSignature')  # Field name made lowercase.
    varoutofbound = models.Float64Field(db_column='VarOutOfBound')  # Field name made lowercase.
    skippedscan = models.Float64Field(db_column='SkippedScan')  # Field name made lowercase.
    battery_min = models.Float64Field(db_column='Battery_Min')  # Field name made lowercase.
    watchdogerrors = models.Float64Field(db_column='WatchdogErrors')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'gruvebadet_Diagnostic'


class Mammamia3Mm3Borehole(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    readezortd_ok = models.Float64Field(db_column='ReadEzoRTD_OK')  # Field name made lowercase.
    bh_recnum = models.Float64Field(db_column='BH_RecNum')  # Field name made lowercase.
    bh_plough_force = models.Float64Field(db_column='BH_Plough_Force')  # Field name made lowercase.
    readkellerld_ok2 = models.Float64Field(db_column='ReadKellerLD_OK2')  # Field name made lowercase.
    atbottom = models.Float64Field(db_column='AtBottom')  # Field name made lowercase.
    icm20948_tilt_z = models.Float64Field(db_column='ICM20948_tilt_z')  # Field name made lowercase.
    icm20948_heading = models.Float64Field(db_column='ICM20948_heading')  # Field name made lowercase.
    bh_chargeinput = models.Float64Field(db_column='BH_ChargeInput')  # Field name made lowercase.
    icm20948_mag_z = models.Float64Field(db_column='ICM20948_mag_z')  # Field name made lowercase.
    tsresult = models.Float64Field(db_column='TSResult')  # Field name made lowercase.
    bh_ptemp = models.Float64Field(db_column='BH_PTemp')  # Field name made lowercase.
    icm20948_heading_comp = models.Float64Field(db_column='ICM20948_heading_comp')  # Field name made lowercase.
    bh_plough_d = models.Float64Field(db_column='BH_Plough_D')  # Field name made lowercase.
    sht4x_temp = models.Float64Field(db_column='SHT4X_Temp')  # Field name made lowercase.
    selectmux_ok = models.Float64Field(db_column='SelectMux_OK')  # Field name made lowercase.
    icm20948_mag_x = models.Float64Field(db_column='ICM20948_mag_x')  # Field name made lowercase.
    kellerx_tob1 = models.Float64Field(db_column='KellerX_TOB1')  # Field name made lowercase.
    triggerresult = models.Float64Field(db_column='TriggerResult')  # Field name made lowercase.
    bh_plough_b = models.Float64Field(db_column='BH_Plough_B')  # Field name made lowercase.
    kellerld_p1 = models.Float64Field(db_column='KellerLD_P1')  # Field name made lowercase.
    readicm20948_ok = models.Float64Field(db_column='ReadICM20948_OK')  # Field name made lowercase.
    icm20948_tilt_y = models.Float64Field(db_column='ICM20948_tilt_y')  # Field name made lowercase.
    surfacetimestamp = models.DateTimeField(db_column='SurfaceTimeStamp')  # Field name made lowercase.
    readkellerld_ok1 = models.Float64Field(db_column='ReadKellerLD_OK1')  # Field name made lowercase.
    bh_battv = models.Float64Field(db_column='BH_BattV')  # Field name made lowercase.
    kellerld_t2 = models.Float64Field(db_column='KellerLD_T2')  # Field name made lowercase.
    ezo_tmp = models.Float64Field(db_column='Ezo_Tmp')  # Field name made lowercase.
    icm20948_acc_z = models.Float64Field(db_column='ICM20948_acc_z')  # Field name made lowercase.
    sht4x_rh = models.Float64Field(db_column='SHT4X_RH')  # Field name made lowercase.
    readkellerld_ok3 = models.Float64Field(db_column='ReadKellerLD_OK3')  # Field name made lowercase.
    bh_plough_a = models.Float64Field(db_column='BH_Plough_A')  # Field name made lowercase.
    kellerld_p3 = models.Float64Field(db_column='KellerLD_P3')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    kellerld_t1 = models.Float64Field(db_column='KellerLD_T1')  # Field name made lowercase.
    proxv = models.Float64Field(db_column='ProxV')  # Field name made lowercase.
    bh_battv_lithium = models.Float64Field(db_column='BH_BattV_Lithium')  # Field name made lowercase.
    kellerx_p1 = models.Float64Field(db_column='KellerX_P1')  # Field name made lowercase.
    ezo_ec = models.Float64Field(db_column='Ezo_EC')  # Field name made lowercase.
    bh_plough_c = models.Float64Field(db_column='BH_Plough_C')  # Field name made lowercase.
    readsht4x_ok = models.Float64Field(db_column='ReadSHT4X_OK')  # Field name made lowercase.
    icm20948_acc_y = models.Float64Field(db_column='ICM20948_acc_y')  # Field name made lowercase.
    icm20948_tilt_x = models.Float64Field(db_column='ICM20948_tilt_x')  # Field name made lowercase.
    icm20948_acc_x = models.Float64Field(db_column='ICM20948_acc_x')  # Field name made lowercase.
    readkellerx_ok = models.Float64Field(db_column='ReadKellerX_OK')  # Field name made lowercase.
    bh_plough_angle = models.Float64Field(db_column='BH_Plough_Angle')  # Field name made lowercase.
    kellerld_p2 = models.Float64Field(db_column='KellerLD_P2')  # Field name made lowercase.
    readezoec_ok = models.Float64Field(db_column='ReadEzoEC_OK')  # Field name made lowercase.
    icm20948_temp = models.Float64Field(db_column='ICM20948_Temp')  # Field name made lowercase.
    icm20948_mag_y = models.Float64Field(db_column='ICM20948_mag_y')  # Field name made lowercase.
    kellerld_t3 = models.Float64Field(db_column='KellerLD_T3')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'mammamia3_mm3_Borehole'


class Mammamia3Mm3Surface(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    plough_d = models.Float64Field(db_column='Plough_D')  # Field name made lowercase.
    ftpfilename_mm3_surface = models.StringField(db_column='FtpFileName_mm3_Surface')  # Field name made lowercase.
    tries = models.Float64Field(db_column='Tries')  # Field name made lowercase.
    ptemp = models.Float64Field(db_column='PTemp')  # Field name made lowercase.
    plough_b = models.Float64Field(db_column='Plough_B')  # Field name made lowercase.
    boreholetimestamp = models.DateTime64Field(db_column='BoreholeTimeStamp', precision=3)  # Field name made lowercase.
    sftimestamp = models.DateTimeField(db_column='SfTimeStamp')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    plough_v1 = models.Float64Field(db_column='Plough_V1')  # Field name made lowercase.
    forcebh_on = models.Float64Field(db_column='ForceBH_On')  # Field name made lowercase.
    force_modem_on = models.Float64Field(db_column='Force_Modem_On')  # Field name made lowercase.
    ftpresult_mm3_borehole = models.Float64Field(db_column='FTPResult_mm3_Borehole')  # Field name made lowercase.
    ftpsend = models.Float64Field(db_column='FtpSend')  # Field name made lowercase.
    bh_trigger = models.Float64Field(db_column='BH_Trigger')  # Field name made lowercase.
    transmittimestamp = models.DateTime64Field(db_column='TransmitTimeStamp', precision=3)  # Field name made lowercase.
    ftpresult_mm3_surface = models.Float64Field(db_column='FTPResult_mm3_Surface')  # Field name made lowercase.
    battv = models.Float64Field(db_column='BattV')  # Field name made lowercase.
    ftpfilename_mm3_borehole = models.StringField(db_column='FtpFileName_mm3_Borehole')  # Field name made lowercase.
    getdataresult = models.Float64Field(db_column='GetDataResult')  # Field name made lowercase.
    boreholerecord = models.Float64Field(db_column='BoreholeRecord')  # Field name made lowercase.
    timeoffset = models.Float64Field(db_column='TimeOffset')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'mammamia3_mm3_Surface'


class Mobileflux2Biomet(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    fc2driftmin_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmin_99_99_1_1_1')  # Field name made lowercase.
    fc2wsmax_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmax_16_99_1_1_1')  # Field name made lowercase.
    fc2driftstd_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTstd_99_99_1_1_1')  # Field name made lowercase.
    precip_diff_d = models.Float64Field(db_column='precip_diff_D')  # Field name made lowercase.
    dc4 = models.Float64Field()
    precip_int_h_d = models.Float64Field(db_column='precip_int_h_D')  # Field name made lowercase.
    dc8 = models.Float64Field()
    precip_type_d = models.Float64Field(db_column='precip_type_D')  # Field name made lowercase.
    fc1driftmax_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmax_99_99_1_1_1')  # Field name made lowercase.
    precip_abs_d = models.Float64Field(db_column='precip_abs_D')  # Field name made lowercase.
    fc2wsmin_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmin_16_99_1_1_1')  # Field name made lowercase.
    dc7 = models.Float64Field()
    dc11 = models.Float64Field()
    fc1wsmax_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmax_16_99_1_1_1')  # Field name made lowercase.
    tot_precip_part = models.Float64Field()
    dc5 = models.Float64Field()
    fc2wsmean_16_99_1_1_1 = models.Float64Field(db_column='FC2WSmean_16_99_1_1_1')  # Field name made lowercase.
    snow_part = models.Float64Field()
    dc6 = models.Float64Field()
    fc1driftsum_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTsum_99_99_1_1_1')  # Field name made lowercase.
    fc1wsmean_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmean_16_99_1_1_1')  # Field name made lowercase.
    fc1wsmin_16_99_1_1_1 = models.Float64Field(db_column='FC1WSmin_16_99_1_1_1')  # Field name made lowercase.
    tot_drops = models.Float64Field()
    fc1driftmin_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmin_99_99_1_1_1')  # Field name made lowercase.
    fc2driftmean_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmean_99_99_1_1_1')  # Field name made lowercase.
    fc2driftsum_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTsum_99_99_1_1_1')  # Field name made lowercase.
    dc10 = models.Float64Field()
    hail_part = models.Float64Field()
    dc0 = models.Float64Field()
    fc2driftmax_99_99_1_1_1 = models.Float64Field(db_column='FC2DRIFTmax_99_99_1_1_1')  # Field name made lowercase.
    dc9 = models.Float64Field()
    fc1driftmean_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTmean_99_99_1_1_1')  # Field name made lowercase.
    dc1 = models.Float64Field()
    fc1driftstd_99_99_1_1_1 = models.Float64Field(db_column='FC1DRIFTstd_99_99_1_1_1')  # Field name made lowercase.
    dc2 = models.Float64Field()
    dc3 = models.Float64Field()
    drizzle_part = models.Float64Field()
    precip_int_min_d = models.Float64Field(db_column='precip_int_min_D')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    t_nr = models.Float64Field(db_column='T_nr')  # Field name made lowercase.
    r_lw_out_meas = models.Float64Field(db_column='R_LW_out_meas')  # Field name made lowercase.
    v_batt = models.Float64Field(db_column='V_batt')  # Field name made lowercase.
    r_sw_in = models.Float64Field(db_column='R_SW_in')  # Field name made lowercase.
    r_lw_in_meas = models.Float64Field(db_column='R_LW_in_meas')  # Field name made lowercase.
    press_amb = models.Float64Field()
    t_amb = models.Float64Field(db_column='T_amb')  # Field name made lowercase.
    rh_amb = models.Float64Field(db_column='RH_amb')  # Field name made lowercase.
    r_sw_out = models.Float64Field(db_column='R_SW_out')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'mobileflux2_Biomet'


class MobilefluxBiomet(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    ts_2_38_3_1_1 = models.Float64Field(db_column='TS_2_38_3_1_1')  # Field name made lowercase.
    sr50distance_9_99_1_1_1 = models.Float64Field(db_column='SR50DISTANCE_9_99_1_1_1')  # Field name made lowercase.
    shf_99_37_1_1_2 = models.Float64Field(db_column='SHF_99_37_1_1_2')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    ta_2_1_1_1_1 = models.Float64Field(db_column='TA_2_1_1_1_1')  # Field name made lowercase.
    lwout_6_15_1_1_1 = models.Float64Field(db_column='LWOUT_6_15_1_1_1')  # Field name made lowercase.
    surfacetemp_2_99_1_1_1 = models.Float64Field(db_column='SURFACETEMP_2_99_1_1_1')  # Field name made lowercase.
    cs650vratio_99_99_3_1_1 = models.Float64Field(db_column='CS650VRATIO_99_99_3_1_1')  # Field name made lowercase.
    sr50quality_99_99_1_1_1 = models.Float64Field(db_column='SR50QUALITY_99_99_1_1_1')  # Field name made lowercase.
    p_rain_8_19_1_1_1 = models.Float64Field(db_column='P_RAIN_8_19_1_1_1')  # Field name made lowercase.
    lwin_6_14_1_1_1 = models.Float64Field(db_column='LWIN_6_14_1_1_1')  # Field name made lowercase.
    rh_19_3_1_1_1 = models.Float64Field(db_column='RH_19_3_1_1_1')  # Field name made lowercase.
    swin_6_10_1_1_1 = models.Float64Field(db_column='SWIN_6_10_1_1_1')  # Field name made lowercase.
    shf_6_37_2_1_1 = models.Float64Field(db_column='SHF_6_37_2_1_1')  # Field name made lowercase.
    shf_6_37_1_1_1 = models.Float64Field(db_column='SHF_6_37_1_1_1')  # Field name made lowercase.
    ts_2_38_2_1_1 = models.Float64Field(db_column='TS_2_38_2_1_1')  # Field name made lowercase.
    shf_99_37_2_1_2 = models.Float64Field(db_column='SHF_99_37_2_1_2')  # Field name made lowercase.
    bec_99_99_3_1_1 = models.Float64Field(db_column='BEC_99_99_3_1_1')  # Field name made lowercase.
    pa_4_2_1_1_1 = models.Float64Field(db_column='PA_4_2_1_1_1')  # Field name made lowercase.
    vin_18_39_1_1_1 = models.Float64Field(db_column='VIN_18_39_1_1_1')  # Field name made lowercase.
    swc_12_36_3_1_1 = models.Float64Field(db_column='SWC_12_36_3_1_1')  # Field name made lowercase.
    cs650period_99_99_3_1_1 = models.Float64Field(db_column='CS650PERIOD_99_99_3_1_1')  # Field name made lowercase.
    swout_6_11_1_1_1 = models.Float64Field(db_column='SWOUT_6_11_1_1_1')  # Field name made lowercase.
    permittivity_99_99_3_1_1 = models.Float64Field(db_column='PERMITTIVITY_99_99_3_1_1')  # Field name made lowercase.
    s_quality = models.Float64Field(db_column='S_quality')  # Field name made lowercase.
    shf_6_36_1_1_1 = models.Float64Field(db_column='SHF_6_36_1_1_1')  # Field name made lowercase.
    pulse_cnr4_tot = models.Float64Field(db_column='pulse_CNR4_Tot')  # Field name made lowercase.
    heatflux_2 = models.Float64Field(db_column='Heatflux_2')  # Field name made lowercase.
    cs650_vwc = models.Float64Field(db_column='CS650_VWC')  # Field name made lowercase.
    shf_cal_2_field = models.Float64Field(db_column='shf_cal(2)')  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    t_nr = models.Float64Field(db_column='T_nr')  # Field name made lowercase.
    rl_up_meas = models.Float64Field(db_column='Rl_up_meas')  # Field name made lowercase.
    tss = models.Float64Field(db_column='TSS')  # Field name made lowercase.
    rh1_19_3_1_1_1 = models.Float64Field(db_column='RH1_19_3_1_1_1')  # Field name made lowercase.
    p_rain1_8_19_1_1_1 = models.Float64Field(db_column='P_RAIN1_8_19_1_1_1')  # Field name made lowercase.
    ta1_2_1_1_1 = models.Float64Field(db_column='TA1_2_1_1_1')  # Field name made lowercase.
    shf_6_36_2_1_1 = models.Float64Field(db_column='SHF_6_36_2_1_1')  # Field name made lowercase.
    rl_down_meas = models.Float64Field(db_column='Rl_down_meas')  # Field name made lowercase.
    s = models.Float64Field(db_column='S')  # Field name made lowercase.
    t_k_nr = models.Float64Field(db_column='T_K_nr')  # Field name made lowercase.
    cs650_bec = models.Float64Field(db_column='CS650_BEC')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'mobileflux_Biomet'


class MobilefluxStationstatus(models.ClickhouseModel):
    timestamp = models.UInt32Field(db_column='TIMESTAMP', primary_key=True)  # Field name made lowercase.
    pulse_cnr4_tot = models.Float64Field(db_column='pulse_CNR4_Tot')  # Field name made lowercase.
    record = models.UInt32Field(db_column='RECORD')  # Field name made lowercase.
    t_nr = models.Float64Field(db_column='T_nr')  # Field name made lowercase.
    shf_cal_on_f = models.Float64Field()
    buff_depth = models.Float64Field()
    panel_tmpr = models.Float64Field()
    shf_cal_1_field = models.Float64Field(db_column='shf_cal(1)')  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    rl_down_meas = models.Float64Field(db_column='Rl_down_meas')  # Field name made lowercase.
    cxtla_tilt_y = models.Float64Field(db_column='CXTLA_tilt_Y')  # Field name made lowercase.
    cxtla_tilt_x = models.Float64Field(db_column='CXTLA_tilt_X')  # Field name made lowercase.
    sw12_1_state = models.Float64Field()
    ftpresult_biomet = models.Float64Field(db_column='FTPResult_Biomet')  # Field name made lowercase.
    licoron = models.Float64Field(db_column='LicorOn')  # Field name made lowercase.
    powlicor = models.Float64Field(db_column='PowLicor')  # Field name made lowercase.
    t_k_nr = models.Float64Field(db_column='T_K_nr')  # Field name made lowercase.
    shf_cal_2_field = models.Float64Field(db_column='shf_cal(2)')  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    rl_up_meas = models.Float64Field(db_column='Rl_up_meas')  # Field name made lowercase.
    batt_cr6 = models.Float64Field(db_column='batt_CR6')  # Field name made lowercase.
    process_time = models.Float64Field()
    ftpresult_stationstatus = models.Float64Field(db_column='FTPResult_StationStatus')  # Field name made lowercase.
    a116_panel_tmpr = models.Float64Field(db_column='A116_panel_tmpr')  # Field name made lowercase.
    batttc = models.Float64Field(db_column='BattTC')  # Field name made lowercase.
    ftpresult_biomet_max = models.Float64Field(db_column='FTPResult_Biomet_Max')  # Field name made lowercase.
    control_mode = models.Float64Field()
    process_time_max = models.Float64Field(db_column='process_time_Max')  # Field name made lowercase.
    buff_depth_max = models.Float64Field(db_column='buff_depth_Max')  # Field name made lowercase.
    ftpresult_stationstatus_max = models.Float64Field(db_column='FTPResult_StationStatus_Max')  # Field name made lowercase.
    control_state = models.Float64Field()
    battv1_sens = models.Float64Field(db_column='BattV1_sens')  # Field name made lowercase.
    d_filt = models.Float64Field()
    ah_tot_hi = models.Float64Field(db_column='Ah_tot_hi')  # Field name made lowercase.
    alarm_lo = models.Float64Field(db_column='Alarm_LO')  # Field name made lowercase.
    ah_tot_low = models.Float64Field(db_column='Ah_tot_low')  # Field name made lowercase.
    ftpresult_biomet_min = models.Float64Field(db_column='FTPResult_Biomet_Min')  # Field name made lowercase.
    ah_hi = models.Float64Field(db_column='Ah_hi')  # Field name made lowercase.
    ah_low = models.Float64Field(db_column='Ah_low')  # Field name made lowercase.
    alarm_hi = models.Float64Field(db_column='Alarm_HI')  # Field name made lowercase.
    buff_depth_avg = models.Float64Field(db_column='buff_depth_Avg')  # Field name made lowercase.
    batt_volt = models.Float64Field()
    regulatorres = models.Float64Field(db_column='RegulatorRes')  # Field name made lowercase.
    battv2 = models.Float64Field(db_column='BattV2')  # Field name made lowercase.
    hour_low = models.Float64Field(db_column='Hour_low')  # Field name made lowercase.
    dip_switch = models.Float64Field()
    batt_i2 = models.Float64Field(db_column='Batt_I2')  # Field name made lowercase.
    fault = models.Float64Field()
    v_ref = models.Float64Field(db_column='V_Ref')  # Field name made lowercase.
    hour_hi = models.Float64Field(db_column='Hour_hi')  # Field name made lowercase.
    battv1_slow = models.Float64Field(db_column='BattV1_slow')  # Field name made lowercase.
    batt_i1 = models.Float64Field(db_column='Batt_I1')  # Field name made lowercase.
    ftpresult_stationstatus_min = models.Float64Field(db_column='FTPResult_StationStatus_Min')  # Field name made lowercase.
    battv1 = models.Float64Field(db_column='BattV1')  # Field name made lowercase.
    process_time_avg = models.Float64Field(db_column='process_time_Avg')  # Field name made lowercase.
    regulatortc = models.Float64Field(db_column='RegulatorTC')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'mobileflux_StationStatus'


class LicorFinseflux(models.ClickhouseModel):
    timestamp = models.DateTime64Field(db_column='TIMESTAMP', precision=3, primary_key=True)

    co2_signal_strength = models.Float64Field(db_column='CO2_Signal_Strength')
    co2_dry_umol_mol = models.Float64Field(db_column='CO2_dry_umol_mol')
    h2o_dry_mmol_mol = models.Float64Field(db_column='H2O_dry_mmol_mol')
    cell_temperature_c = models.Float64Field(db_column='Cell_Temperature_C')
    diagnostic_value = models.Float64Field(db_column='Diagnostic_Value')
    temperature_out_c = models.Float64Field(db_column='Temperature_Out_C')
    aux_2_v_m_s = models.Float64Field(db_column='Aux_2_V_m_s')
    total_pressure_kpa = models.Float64Field(db_column='Total_Pressure_kPa')
    aux_1_u_m_s = models.Float64Field(db_column='Aux_1_U_m_s')
    h2o_signal_strength = models.Float64Field(db_column='H2O_Signal_Strength')
    aux_3_w_m_s = models.Float64Field(db_column='Aux_3_W_m_s')
    flow_rate_lpm = models.Float64Field(db_column='Flow_Rate_lpm')
    co2_mmol_m_3 = models.Float64Field(db_column='CO2_mmol_m_3')
    average_signal_strength = models.Float64Field(db_column='Average_Signal_Strength')
    h2o_mmol_m_3 = models.Float64Field(db_column='H2O_mmol_m_3')
    chk = models.Float64Field(db_column='CHK')
    delta_signal_strength = models.Float64Field(db_column='Delta_Signal_Strength')
    aux_4_sos_m_s = models.Float64Field(db_column='Aux_4_SOS_m_s')
    temperature_in_c = models.Float64Field(db_column='Temperature_In_C')
    diagnostic_value_2 = models.Float64Field(db_column='Diagnostic_Value_2')

    class Meta:
        managed = False
        db_table = 'licor_finseflux'
