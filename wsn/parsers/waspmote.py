'''
Script to parse frames from waspmote

Simon Filhol, J. David Ibáñez
'''

# Standard Library
import itertools
import math
import struct

from Crypto.Cipher import AES


def post_noop(value):
    return value

def post_acc(value):
    if (value > 1000): value = 1000
    if (value < -1000): value = -1000
    return (180/math.pi) * math.asin(value/1000)

def post_ds1820(value):
    #f = lambda x: x if (-100 < x < 100) else None # None if out of range
    #values = [f(value / 16) for value in values]
    return [value / 16 for value in value]


"""
f - float
j - int16_t
u - uint8_t
w - uint32_t
s - char*
n - Array of int16_t (specially compressed)
"""

SENSORS = {
     15: ('f', ['pa']),                                  # Legacy (agr board: pressure)
     33: ('f', ['tcb']),                                 # Legacy (agr board: temperature)
     35: ('f', ['humb']),                                # Legacy (agr board: humidity)
     38: ('f', ['lw']),                                  # Legacy (agr board: leaf-wetness)
     52: ('u', ['bat']),                                 # Battery level %
     53: ('ff', ['latitude', 'longitude']),              # GPS location
     54: ('j', ['rssi']),                                # RSSI
     55: ('s', ['mac']),                                 # Legacy (MAC address)
     62: ('f', ['in_temp']),                             # Legacy (v12 RTC: internal temp)
     63: ('jjj', ['acc_x', 'acc_y', 'acc_z'], post_acc), # Accelerometer
     65: ('s', ['str']),                                 # Legacy (string field)
     74: ('f', ['bme_tc']),                              # Legacy (BME, see 210)
     76: ('f', ['bme_hum']),                             # Legacy (BME, see 210)
     77: ('f', ['bme_pres']),                            # Legacy (BME, see 210)
     85: ('u', ['tx_pwr']),                              # Legacy (transmission power)
     91: ('f', ['altitude']),                            # GPS altitude
    123: ('w', ['tst']),                                 # Time stamp (epoch)
    200: ('fff', ['ctd_depth', 'ctd_temp', 'ctd_cond']), # CTD-10
    201: ('fff', ['ds2_speed', 'ds2_dir', 'ds2_temp']),  # Legacy (DS-2, see 208)
    202: ('fff', ['ds2_meridional', 'ds2_zonal', 'ds2_gust']), # Legacy (DS-2, see 208)
    203: ('n', ['ds1820'], post_ds1820),                 # DS18B20 string, array of temperatures
    204: ('ww', ['mb_median', 'mb_sd']),                 # Legacy (MB73XX, see 214)
    205: ('uf', ['gps_satellites', 'gps_accuracy']),     # GPS number of satellites and (horizontal) accuracy
    206: ('f', ['volts']),                               # Battery level volts
    207: ('fffuf', ['precip_abs', 'precip_dif', 'precip_int_h', 'precip_type', 'precip_int_min']), # WS-100
    208: ('ffffff', ['ds2_speed', 'ds2_dir', 'ds2_temp', 'ds2_meridional', 'ds2_zonal', 'ds2_gust']), # DS-2 (wind)
    209: ('fff', ['int_tc', 'int_hum', 'int_pres']),     # BME internal 0x76
    210: ('fff', ['bme_tc', 'bme_hum', 'bme_pres']),     # BME external 0x77
    211: ('ff', ['mlx_object', 'mlx_ambient']),          # MLX90614 temperature
    212: ('f', ['tmp_temperature']),                     # TMP102 temperature
    213: ('n', ['vl_distance']),                         # VL53L1X distance
    214: ('n', ['mb_distance']),                         # MB73XX array of distances
    215: ('ffffff', ['wind_speed', 'wind_dir', 'wind_gust', 'wind_temp', 'wind_x', 'wind_y']), # ATMOS (wind)
}


def unpack(n, iterable):
    infinite = itertools.chain(iterable, itertools.repeat(None))
    return itertools.islice(infinite, n)


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


ciphers = {}
def get_cipher(key):
    if key is None:
        return None

    cipher = ciphers.get(key)
    if cipher is None:
        cipher = AES.new(key, AES.MODE_ECB)
        ciphers[key] = cipher

    return cipher


def parse_frame(src, cipher_key=None):
    """
    Parse the frame starting at the given byte string. We consider that the
    frame start delimeter has already been read.
    """
    line = src

    if cipher_key is not None and type(cipher_key) is not bytes:
        raise TypeError('cipher_key must be None or bytes, got %s' % type(cipher_key))

    # Start delimiter
    if not line.startswith(b'<=>'):
        print('Warning: expected frame not found')
        return None, src

    line = line[3:]

    # Frame type
    frame_type = struct.unpack_from("B", line)[0]
    line = line[1:]

    if frame_type & 128: # b7
        print("Warning: text frames not supported (%d)" % frame_type)
        return None, src

    if frame_type == 96:
        encrypted = True
        v15 = True
    elif 96 < frame_type < 100:
        encrypted = True
        v15 = False
    elif frame_type > 11:
        print("Warning: %d frame type not supported" % frame_type)
        return None, src
    else:
        encrypted = False
        # 0 -  5 : v12
        # 6 - 11 : v15
        # From 7 to 11 are "Reserved types" in Libellium's lib. But we use the
        # event type, and need to tell apart v12 from v15 (otherwise we cannot
        # know whether the serial number is 32 or 64 bits long).
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

    # Encrypted
    if encrypted:
        if not v15:
            name, line = line.split(b'#', 1)
            name = name.decode()

        cipher = get_cipher(cipher_key)
        if cipher is None:
            print('Warning: encrypted frames not supported because no key provided')
            return None, src

        line = cipher.decrypt(line)
        frame, _ = parse_frame(line) # _ may contain zeroes
        if frame['serial'] != serial_id:
            print("Warning: serial numbers do not match %d != %d", serial_id, frame['serial'])
            return None, src

        if not v15 and frame['name'] != name:
            print("Warning: name do not match %s != %s", name, frame['name'])
            return None, src

        return frame, rest

    # Name
    name, line = line.split(b'#', 1)
    name = name.decode() # bytes to str
    # Sequence
    sequence = struct.unpack_from("B", line)[0]
    line = line[1:] # Payload

    frame['serial'] = serial_id
    frame['frame'] = sequence # Frame sequence
    frame['name'] = name

    while line:
        sensor_id = struct.unpack_from("B", line)[0]
        line = line[1:]
        sensor = SENSORS.get(sensor_id, ())
        if not sensor:
            print("Warning: %d sensor type not supported" % sensor_id)
            return None, src

        form, names, post = unpack(3, sensor)
        if post is None:
            post = post_noop

        for c, name in zip(form, names):
            name = name.lower()
            if c == 'f':
                value = struct.unpack_from("f", line)[0]
                line = line[4:]
            elif c == 'j':
                value = struct.unpack_from("h", line)[0]
                line = line[2:]
            elif c == 'u':
                value = struct.unpack_from("B", line)[0]
                line = line[1:]
            elif c == 'v':
                value = struct.unpack_from("H", line)[0]
                line = line[2:]
            elif c == 'w':
                value = struct.unpack_from("I", line)[0]
                line = line[4:]
            elif c == 'str':
                length = struct.unpack_from("B", line)[0]
                line = line[1:]
                value = line[:length]
                line = line[length:]
            elif c == 'n':
                # Variable list of values (done for the DS18B20 string)
                values = []
                n_values = struct.unpack_from("B", line)[0]
                line = line[1:]
                for j in range(n_values):
                    if j > 0:
                        value = struct.unpack_from("b", line)[0]
                        line = line[1:]
                        if value != -128:
                            value = values[-1] + value
                            values.append(value)
                            continue

                    value = struct.unpack_from("h", line)[0]
                    line = line[2:]
                    values.append(value)

                value = frame.get(name, []) + values

            frame[name] = post(value)

    return frame, rest


def read_wasp_data(f):
    src = f.read()

    while src:
        bad, good = search_frame(src)
        if bad:
            print('Warning: %d bytes of garbage found and discarded' % len(bad))
            print(bad[:50])

        if good:
            frame, src = parse_frame(good)
            if frame is None:
                break

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

    return {'tags': tags, 'frames': [{'time': time, 'data': data}]}
