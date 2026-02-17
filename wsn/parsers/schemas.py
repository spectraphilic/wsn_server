import dataclasses
import math
from typing import Optional


@dataclasses.dataclass
class Field:
    type: str = 'Float64 DEFAULT NaN'
    source: Optional[str] = None  # original name in source file


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
        # Renamed - output name is key, source is original name
        'U_ana': Field(source='Aux 1 - U (m/s)'),
        'V_ana': Field(source='Aux 2 - V (m/s)'),
        'W_ana': Field(source='Aux 3 - W (m/s)'),
        'SOS_ana': Field(source='Aux 4 - SOS (m/s)'),
        'AGC': Field(source='Average Signal Strength'),
        'CO2_dry': Field(source='CO2 dry(umol/mol)'),
        'CO2': Field(source='CO2 (mmol/m^3)'),
        'H2O_dry': Field(source='H2O dry(mmol/mol)'),
        'H2O': Field(source='H2O (mmol/m^3)'),
        'T_in': Field(source='Temperature In (C)'),
        'T_out': Field(source='Temperature Out (C)'),
        'Ptotal': Field(source='Total Pressure (kPa)'),
        # Explicit mappings for fields that were auto-cleaned before
        'Diagnostic_Value': Field(source='Diagnostic Value'),
        'Diagnostic_Value_2': Field(source='Diagnostic Value 2'),
        'Cell_Temperature_C': Field(source='Cell Temperature (C)'),
        'CO2_Signal_Strength': Field(source='CO2 Signal Strength'),
        'H2O_Signal_Strength': Field(source='H2O Signal Strength'),
        'Delta_Signal_Strength': Field(source='Delta Signal Strength'),
        'Flow_Rate_lpm': Field(source='Flow Rate (lpm)'),
        'CHK': Field(),
    },
    'licor_mobileflux': {
        'TIMESTAMP': Field(type="DateTime64(3, 'UTC')"),
        # Renamed - output name is key, source is original name
        'SOS': Field(source='SOS (m/s)'),
        'Ux': Field(source='U (m/s)'),
        'Uy': Field(source='V (m/s)'),
        'Uz': Field(source='W (m/s)'),
        'H2O': Field(source='H2O (mmol/m^3)'),
        'H2O_dry': Field(source='H2O dry(mmol/mol)'),
        'CO2': Field(source='CO2 (mmol/m^3)'),
        'CO2_dry': Field(source='CO2 dry(umol/mol)'),
        'T_in': Field(source='Temperature In (C)'),
        'T_out': Field(source='Temperature Out (C)'),
        'Ptotal': Field(source='Total Pressure (kPa)'),
        'AGC': Field(source='Average Signal Strength'),
        'CH4_mmol_m3': Field(source='CH4 (mmol/m^3)'),
        'CH4_umol_mol': Field(source='CH4 (umol/mol)'),
        'CH4_Temperature': Field(source='CH4 Temperature'),
        'CH4_Pressure': Field(source='CH4 Pressure'),
        'CH4_Signal_Strength': Field(source='CH4 Signal Strength'),
    },
    'default': {
        'TIMESTAMP': Field(type='UInt32'),
        'RECORD': Field(type='UInt32'),
    },
}


class Schema:

    def __init__(self, name, strict: bool = False):
        self.schema_data = SCHEMAS[name]
        self.strict = strict
        # Build source -> output name mapping for parsers
        self._source_map = {
            field.source: output_name
            for output_name, field in self.schema_data.items()
            if field is not None and field.source is not None
        }

    def get_output_name(self, source_name):
        """
        Map source name to output name.
        If explicit mapping exists, return it.
        Otherwise, return None (strict) or the source name unchanged (non-strict).
        """
        # Check explicit mapping first
        if source_name in self._source_map:
            return self._source_map[source_name]

        # No explicit mapping found
        if self.strict:
            return None

        # Non-strict: return as-is
        return source_name

    def get_field(self, name):
        """
        Get field by output name (the key in schema).
        Returns None if not found and strict=True.
        """
        if name not in self.schema_data:
            if self.strict:
                return None
            # In non-strict mode, return default field
            return Field()

        return self.schema_data[name]

    def get_value(self, name, value):
        field = self.get_field(name)
        if field is None:
            return None

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
