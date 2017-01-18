import time
from sense_hat import SenseHat
from influxdb import InfluxDBClient
import system_metrics as sysmet
import subprocess
import re
import logging
import threading

DATABASE = 'rpdemo'
PING_HOST = 'google.com.au'
last_ping_time = 0.0

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

def async_ping(host):
    '''
    use a thread to run ping (which blocks) to the given host
    the result is set into global last_ping_time (ms)
    '''
    # TODO: use multiprocessing.pool.ThreadPool?
    # http://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python
    def do_ping(host):
        global last_ping_time
        last_ping_time = ping(host)

    t = threading.Thread(target=do_ping, args=(host,))
    # we don't want this thread to stop the main thread from exiting
    t.setDaemon(True)
    t.start()

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
    fields = {
        'ping_google': last_ping_time
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
        points = build_points()
        logging.debug(str(points))
        influx.write_points(points)

        # run ping in worker thread, result goes to global last_ping_time
        async_ping(PING_HOST)

        time.sleep(1)
