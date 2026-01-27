import dataclasses
import math
from typing import Optional


@dataclasses.dataclass
class Field:
    type: str = 'Float64 DEFAULT NaN'
    name: Optional[str] = None

SCHEMAS = {
    'mammamia3': {
        'TIMESTAMP': Field(type='UInt32'),
        'RECORD': Field(type='UInt32'),
        # Borehole
        'SurfaceTimeStamp': Field(type="DateTime('UTC')"),
        # Surface
        'BoreholeTimeStamp': Field(type="DateTime64(3, 'UTC')"),
        'FtpFileName_mm3_Borehole': Field(type='String'),
        'FtpFileName_mm3_Surface': Field(type='String'),
        'SfTimeStamp': Field(type="DateTime('UTC')"),
        'TransmitTimeStamp': Field(type="DateTime64(3, 'UTC')"),
    },
    'gruvebadet': {
        'TIMESTAMP': Field(type='UInt32'),
        'RECORD': Field(type='UInt32'),
        # Diagnostics
        'CompileResults': Field(type='String'),
        'OSVersion': Field(type='String'),
        'ProgName': Field(type='String'),
        'StartTime': Field(type="DateTime64(3, 'UTC')"),
    },
    'hfdata': {
        'TIMESTAMP': Field(type="DateTime64(3, 'UTC')"),
        'RECORD': Field(type='UInt32'),
    },
    'licor_finseflux': {
        'TIMESTAMP': Field(type="DateTime64(3, 'UTC')"),
        # Skipped
        'DATAH': None,
        'DATE': None,
        'TIME': None,
        'Seconds': None,
        'Nanoseconds': None,
        'Date': None,
        'Time': None,
        # Renamed
        'Aux 1 - U (m/s)': Field(name='U_ana'),
        'Aux 2 - V (m/s)': Field(name='V_ana'),
        'Aux 3 - W (m/s)': Field(name='W_ana'),
        'Aux 4 - SOS (m/s)': Field(name='SOS_ana'),
        'Average Signal Strength': Field(name='AGC'),
        'CO2 dry(umol/mol)': Field(name='CO2_dry'),
        'CO2 (mmol/m^3)': Field(name='CO2'),
        'H2O dry(mmol/mol)': Field(name='H2O_dry'),
        'H2O (mmol/m^3)': Field(name='H2O'),
        'Temperature In (C)': Field(name='T_in'),
        'Temperature Out (C)': Field(name='T_out'),
        'Total Pressure (kPa)': Field(name='Ptotal'),
    },
    'default': {
        'TIMESTAMP': Field(type='UInt32'),
        'RECORD': Field(type='UInt32'),
    },
}

class Schema:

    def __init__(self, name):
        self.schema_data = SCHEMAS[name]

    def get_field(self, name):
        if name not in self.schema_data:
            return Field(name=name)

        return self.schema_data[name]

    def get_value(self, name, value):
        field = self.get_field(name)
        if field.type.startswith('Float64'):
            try:
                return float(value)
            except ValueError:
                # In HFData files, e.g. "-" (U_ana) or "" (sonic_diag)
                return math.nan

        types = [int, float, str]
        for t in types:
            try:
                return t(value)
            except ValueError:
                pass

        return None
