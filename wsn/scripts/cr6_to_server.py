#!/usr/bin/env python3

"""
Deploy this script manually, copy it to /usr/local/bin

Install requirements system-wide:

    # apt-get install python3-requests

For every user where CR6 files are being uploaded, add a crontab file
with the following contents:

    WSN_URL=https://latice.eu/wsn/api/create/
    WSN_TOKEN=XXX

    */30 * * * * /usr/local/bin/cr6_to_server.py /home/xxx/upload/*.dat
"""


import argparse
import csv
from datetime import datetime, timezone
import lzma
import os
import sys
import time
import traceback

import requests


def convert(value, unit):
    if unit == 'TS':
        value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    # JSON does not support NAN
    if value == 'NAN':
        return value

    try:
        return int(value)
    except ValueError:
        return float(value)


def handle(filename):

    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
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

        frames = []
        for row in reader:
            data = {}
            for i, value in enumerate(row):
                name = fields[i]
                value = convert(value, units[i])
                if name == 'TIMESTAMP':
                    time = value
                else:
                    data[name] = value

            frames.append({'time': time, 'data': data})

    data = {'tags': tags, 'frames': frames}
    response = requests.post(URL, json=data, headers=HEADERS)
    status = response.status_code
    assert status == 201, '{} {}'.format(status, response.json())


def archive(filename):
    data = open(filename, 'rb').read()
    with lzma.open(filename + '.xz', 'w') as f:
        f.write(data)
    os.remove(filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs="+")
    args = parser.parse_args()

    URL = os.getenv('WSN_URL', 'http://localhost:8000/wsn/api/create/')
    TOKEN = os.getenv('WSN_TOKEN') # Secret, do not define a default
    HEADERS = {'Authorization': 'Token %s' % TOKEN}

    if TOKEN is None:
        print('Define the authenticaton token, for example:')
        print('  export WSN_TOKEN=XXX')
        sys.exit(1)

    for filename in args.filenames:
        # If the file has been modified within the last 15min, skip it. This is
        # a safety measure, just in case the file has not been completely
        # uploaded.
        if  os.stat(filename).st_mtime > (time.time() - 60 * 15):
            print("{} skip for now, will handle later".format(filename))
            continue

        try:
            handle(filename)
        except Exception:
            print("{} ERROR".format(filename))
            traceback.print_exc()
        else:
            print("{} file uploaded".format(filename))
            archive(filename)
            print("{} file archived".format(filename))
