import datetime
import time
from sense_hat import SenseHat
from influxdb import InfluxDBClient
import system_metrics as sysmet
import subprocess
import re
import logging

DATABASE = 'rpdemo'
SAMPLE_INTERVAL = 5.0
PING_GOOGLE_HOST = 'google.com.au'

sense = SenseHat()

def ping(host):
    '''
    ping the given host.
    returns the ping time in ms, or zero if ping fails for any reason
    '''
    ping_time = 0.0
    try:
        # args:  -c1 - send one ping
        #        -w1 - timeout after 1 second
        output = subprocess.check_output(['ping', '-c1', '-w1', host])
        # if any pings got through the last line shows the ping times:
        #   rtt min/avg/max/mdev = 13.965/13.965/13.965/0.000 ms
        # we capture the avg time
        pattern = r'.*rtt.* = .+/(.+)/.+/.+ ms'
        match = re.search(pattern, output)
        if match:
            ping_time = float(match.group(1))
            logging.debug('ping {0} -> {1} ms'.format(host, ping_time))
        else:
            raise ValueError('failed to parse ping output', output)
    except subprocess.CalledProcessError:
        logging.debug('ping {0} failed'.format(host))
        pass

    return ping_time

def build_system_point():
    loadavg = sysmet.get_loadavg()

    fields = {
        'loadavg1': loadavg[1]
    }

    point = {
        'measurement': 'system',
        'fields': fields
    }

    return point

def build_sensehat_point():
    fields = {
        'temperature': float(sense.get_temperature()),
        'humidity': float(sense.get_humidity()),
        'pressure': float(sense.get_pressure())
    }

    point = {
        'measurement': 'sensehat',
        'fields': fields
    }

    return point

def build_net_point():
    # we use ping with a 1 second timeout, which means if the host
    # is not answering this call may take up to 1 second to return
    ping_google = ping(PING_GOOGLE_HOST)

    fields = {
        'ping_google': ping_google
    }

    point = {
        'measurement': 'net',
        'fields': fields
    }

    return point

def build_points():
    points = [
        build_system_point(),
        build_sensehat_point(),
        build_net_point()
    ]
    return points

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    influx = InfluxDBClient('localhost', 8086)

    influx.create_database(DATABASE)
    influx.switch_database(DATABASE)

    while True:
        start_timestamp = datetime.datetime.now()

        points = build_points()

        built_timestamp = datetime.datetime.now()
        logging.debug('built points in {0} ms'.format((built_timestamp - start_timestamp).total_seconds()*1000))
        logging.debug(str(points))

        influx.write_points(points)
        wrote_timestamp = datetime.datetime.now()
        logging.debug('wrote points in {0} ms'.format((wrote_timestamp-built_timestamp).total_seconds()*1000))

        sleep_time_sec = SAMPLE_INTERVAL - (datetime.datetime.now() - start_timestamp).total_seconds()
        time.sleep(sleep_time_sec)

