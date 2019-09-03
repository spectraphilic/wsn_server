import datetime
import os
import pprint
import requests

URL = 'https://wsn.latice.eu/api/query/v2/'
URL = 'http://localhost:8000/api/query/v2/'


# We need an authentication token
TOKEN = os.getenv('WSN_TOKEN', 'dcff0c629050b5492362ec28173fa3e051648cb1')


def query(
    limit=100,           # Pagination
    fields=None,         # Fields to return (all by default)
    tags=None,           # Tags to return (all by default)
    interval=None,       # If given will return the average in the interval
    debug=False,         # Not sent to the API
    # Filters
    time__gte=None, time__lte=None, # Time is special
    **kw):

    # Parameters
    if time__gte:
        time__gte = int(time__gte.timestamp())
    if time__lte:
        time__lte = int(time__lte.timestamp())

    params = {
        'limit': limit,                                 # Pagination
        'time__gte': time__gte, 'time__lte': time__lte, # Time filter
        'fields': fields,
        'tags': tags,
        'interval': interval,
    }

    # Filter inside json
    for key, value in kw.items():
        if value is None:
            params[key] = None
            continue

        if type(value) is datetime.datetime:
            value = int(value.timestamp())

        if isinstance(value, int):
            key += ':int'

        params[key] = value

    # Query
    headers = {'Authorization': 'Token %s' % TOKEN}
    response = requests.get(URL, headers=headers, params=params)
    response.raise_for_status()
    json = response.json()

    # Debug
    if debug:
        pprint.pprint(params)
        pprint.pprint(json)
        print()

    return json


if __name__ == '__main__':
    # Number of elements to return in every query
    limit = 2

    # Example 1: Get all the fields and tags of a given mote from a given time.
    # This is good to explore the data, but bad on performance.
    print('==============================================')
    response = query(limit=limit,
        serial=0x1F566F057C105487,
        time__gte=datetime.datetime(2017, 11, 15),
        debug=True,
    )

    # Example 2: Get the RSSI of an Xbee module identified by its address
    print('==============================================')
    response = query(limit=limit,
        source_addr_long=0x0013A2004105D4B6,
        fields=['rssi'],
        debug=True,
    )

    # Example 3: Get the battery and internal temperature from all motes,
    # include the serial tag to tell them apart.
    # Frames that don't have at least one of the fields we ask for will not be
    # included.
    print('==============================================')
    response = query(limit=limit,
        fields=['bat', 'in_temp'],
        tags=['serial'],
        debug=True,
    )

    # Example 4: Get the time the frame was received by the Pi
    print('==============================================')
    response = query(limit=limit,
        serial=408520806,
        fields=['received'],
        debug=True,
    )

    # Example 5: Get the battery once every hour
    print('==============================================')
    response = query(limit=10,
        serial=0x1F566F057C105487,
        fields=['bat'],
        interval=3600,
        debug=True,
    )

    # Example 6: Query by name
    print('==============================================')
    response = query(limit=limit,
        name='v15@CS',
        time__gte=datetime.datetime(2017, 11, 15),
        debug=True,
    )

    # Example 7: ClickHouse, check available column names
    print('==============================================')
    response = query(limit=1,
        table='finseflux_Biomet',
        debug=True,
    )

    # Example 8: ClickHouse, select some columns
    print('==============================================')
    response = query(limit=limit,
        table='finseflux_Biomet',
        fields=['LWIN_6_14_1_1_1', 'LWOUT_6_15_1_1_1'],
        time__gte=datetime.datetime(2019, 3, 1),
        debug=True,
    )

    # Example 9: ClickHouse, interval returns averages
    print('==============================================')
    response = query(limit=limit,
        table='finseflux_Biomet',
        fields=['LWIN_6_14_1_1_1', 'LWOUT_6_15_1_1_1'],
        time__gte=datetime.datetime(2019, 3, 1),
        interval=3600,
        debug=True,
    )

    # Example 10: ClickHouse, use a different aggregate
    print('==============================================')
    response = query(limit=limit,
        table='finseflux_Biomet',
        fields=['LWIN_6_14_1_1_1', 'LWOUT_6_15_1_1_1'],
        time__gte=datetime.datetime(2019, 3, 1),
        interval=3600,
        interval_agg='min',
        debug=True,
    )
