'''
Script to parse frames from waspmote

Simon Filhol
'''

from datetime import datetime, timezone
import os
import struct


USHORT = 0 # uint8_t
INT    = 1 # int16_t
FLOAT  = 2 # double
STR    = 3 # char*
ULONG  = 4 # uint32_t
LIST_INT = 5 # Array of integers

SENSORS = {
     15: (b'PA', FLOAT, ['pa']),
     33: (b'TCB', FLOAT, ['tcb']),
     35: (b'HUMB', FLOAT, ['humb']),
     38: (b'LW', FLOAT, ['lw']),
     52: (b'BAT', USHORT, ['bat']),
     53: (b'GPS', FLOAT, ['latitude', 'longitude']),
     54: (b'RSSI', INT, ['rssi']),
     55: (b'MAC', STR, ['mac']),
     62: (b'IN_TEMP', FLOAT, ['in_temp']),
#    63: (b'ACC', ),
     65: (b'STR', STR, ['str']),
     74: (b'BME_TC', FLOAT, ['bme_tc']),
     76: (b'BME_HUM', FLOAT, ['bme_hum']),
     77: (b'BME_PRES', FLOAT, ['bme_pres']),
     85: (b'TX_PWR', USHORT, ['tx_pwr']),
#    89: (b'SPEED_OG', ),
#    90: (b'COURSE_OG', ),
#    91: (b'ALT', ),
    123: (b'TST', ULONG, ['tst']),
    200: (b'SDI12_CTD10', FLOAT, ['ctd_depth', 'ctd_temp', 'ctd_cond']),
    201: (b'SDI12_DS2_1', FLOAT, ['ds2_speed', 'ds2_dir', 'ds2_temp']),
    202: (b'SDI12_DS2_2', FLOAT, ['ds2_meridional', 'ds2_zonal', 'ds2_gust']),
    203: (b'DS18B20', LIST_INT, 'ds1820'),
    204: (b'MB73XX', ULONG, ['mb_median', 'mb_sd']),
    206: (b'VOLTS', FLOAT, ['volts']),
}

SENSORS_STR = {v[0]: v for k, v in SENSORS.items()}


def search_frame(data):
    """
    Search the frame starting with the delimiter <=>, return a tuple with:

    - the data found before the delimiter (garbage)
    - the data starting from the delimiter
    """
    # End of data
    if not data:
        return '', ''

    index = data.find(b'<=>')

    # Not found
    if index == -1:
        return data, ''

    if index > 0:
        return data[:index], data[index:]

    return '', data


def parse_frame(line):
    """
    Parse the frame starting at the given byte string. We consider that the
    frame start delimeter has already been read.
    """

    # Start delimiter
    if not line.startswith(b'<=>'):
        print('Warning: expected frame not found')
        return None

    line = line[3:]

    # Frame type
    frame_type = struct.unpack_from("B", line)[0]
    line = line[1:]

    # Frame types
    # 0 -  5 : v12
    # 6 - 11 : v15
    # From 7 to 11 are "Reserved types" in Libellium's lib. But we use the
    # event type, and need to tell apart v12 from v15 (otherwise we cannot know
    # whether the serial number is 32 or 64 bits long).
    if frame_type > 11:
        print("Warning: %d frame type not supported" % frame_type)
        return None

    v15 = frame_type > 5
    if v15:
        # Discard version
        # From 0 (info) to 5 (low battery). We only use 0 and 2
        frame_type -= 6
    frame = {'type': frame_type}

    # Number of bytes (Binary)
    n = struct.unpack_from("B", line)[0]
    line = line[1:]
    rest = line[n:]
    line = line[:n]

    # Serial id
    if v15:
        serial_id = struct.unpack_from(">Q", line)[0]
        line = line[8:]
    else:
        serial_id = struct.unpack_from(">I", line)[0]
        line = line[4:]

    waspmote_id, line = line.split(b'#', 1)
    sequence = struct.unpack_from("B", line)[0]
    line = line[1:] # Payload

    frame['serial'] = serial_id
    frame['frame'] = sequence # Frame sequence
    frame['name'] = waspmote_id.decode() # bytes to str

    while line:
        sensor_id = struct.unpack_from("B", line)[0]
        line = line[1:]
        sensor = SENSORS.get(sensor_id, ())
        if not sensor:
            print("Warning: %d sensor type not supported" % sensor_id)
            return None

        key, sensor_type, names = sensor

        # Variable list of values (done for the DS18B20 string)
        if sensor_type == LIST_INT:
            name = names.lower()
            values = []
            n_values = struct.unpack_from("B", line)[0]
            line = line[1:]
            for i in range(n_values):
                if i > 0:
                    value = struct.unpack_from("b", line)[0]
                    line = line[1:]
                    if value != -128:
                        value = values[-1] + value
                        values.append(value)
                        continue

                value = struct.unpack_from("h", line)[0]
                line = line[2:]
                values.append(value)

            # DS18B20
            if key == b'DS18B20':
                #f = lambda x: x if (-100 < x < 100) else None # None if out of range
                #values = [f(value / 16) for value in values]
                values = [value / 16 for value in values]

            frame[name] = frame.get(name, []) + values
            continue

        # Fixed number of values
        for name in names:
            if sensor_type == USHORT:
                value = struct.unpack_from("B", line)[0]
                line = line[1:]
            elif sensor_type == INT:
                value = struct.unpack_from("h", line)[0]
                line = line[2:]
            elif sensor_type == FLOAT:
                value = struct.unpack_from("f", line)[0]
                line = line[4:]
            elif sensor_type == ULONG:
                value = struct.unpack_from("I", line)[0]
                line = line[4:]
            elif sensor_type == STR:
                length = struct.unpack_from("B", line)[0]
                line = line[1:]
                value = line[:length]
                line = line[length:]

            frame[name.lower()] = value

    return frame, rest


def read_wasp_data(f):
    src = f.read()

    while src:
        bad, good = search_frame(src)
        if bad:
            print('Warning: %d bytes of garbage found and discarded' % len(bad))
            print(bad[:50])

        if good:
            aux = parse_frame(good)
            if aux is None:
                break

            frame, src = aux
            yield frame

            # read end of frame: \n
            if src and src[0] == '\n':
                src = src[1:]


def data_to_json(data):
    """
    Adapt the data to the structure expected by Django.
    """
    # Tags
    tags = {}
    for key in 'source_addr_long', 'serial', 'name':
        value = data.pop(key, None)
        if value is not None:
            tags[key] = value

    # Time
    time = data.pop('tst', None)
    if time is None:
        time = data['received']
    time = datetime.fromtimestamp(time, timezone.utc).isoformat()

    return {'tags': tags, 'frames': [{'time': time, 'data': data}]}


#
# Old code that may be removed
# May still be usefull if we want to plot raw files
#

class frameObj(object):
    def __init__(self, kw):
        # Set defaults (XXX Do we need this?)
        import numpy as np
        self.tst = np.nan
        self.bat = np.nan
        self.tcb = np.nan
        self.in_temp = np.nan
        self.humb = np.nan

        for key, value in kw.items():
            setattr(self, key, value)


def read_wasp_file(filename, data):
    with open(filename, 'rb') as f:
        for frame in read_wasp_data(f):
            frame = frameObj(frame)
            data.append(frame.__dict__)


if __name__ == '__main__':
    import pandas as pd
    #import matplotlib as mpl
    #mpl.use('PS')
    import matplotlib.pyplot as plt

    names = [
#       '../../data/data_20170710/TMP.TXT',
#       '../../data/data_20170710/DATA/170706.TXT',

        #'test/170925/DATA',
        #'test/170926/DATA',
        #'test/170929/DATA',
        #'test/171002/DATA',
        'test/171107/DATA',

        #'test/middalselvi/20171010/DATA',

#       'test/170924-finse/DATA/170921.TXT',
#       'test/170924-finse/DATA/170922.TXT',
#       'test/170924-finse/DATA/170923.TXT',
#       'test/170924-finse/DATA/170924.TXT',
    ]

    data = []
    for name in names:
        if os.path.isdir(name):
            for filename in os.listdir(name):
                filename = os.path.join(name, filename)
                read_wasp_file(filename, data)
        else:
            read_wasp_file(name, data)
    data_frame = pd.DataFrame(data)

    data_frame.sort_values(by='tst', inplace=True)
    data_frame['timestamp'] = pd.to_datetime(data_frame['tst'], unit='s')
    data_frame = data_frame.set_index('timestamp')

    #plt.ion()

    # CTD
    graphs = [
        ('bat', 'Battery level (%)'),
        ('in_temp', 'Internal Temperature (degC)'), # tcb
        #('ctd_depth', 'CTD Water depth'),
        #('ctd_temp', 'CTD Water temperature'),
        #('ctd_cond', 'CTD Water conductivity')
    ]
    fig, ax = plt.subplots(len(graphs), sharex=True)
    for i, (name, title) in enumerate(graphs):
        getattr(data_frame, name).dropna().plot(ax=ax[i])
        ax[i].set_title(i)

    # Plot
    plt.plot()
    plt.show()
