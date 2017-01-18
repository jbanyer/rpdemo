import datetime
import time
from influxdb import InfluxDBClient
import subprocess
import re
import logging
from system_sampler import SystemSampler
from wemo_sampler import WemoSampler
from settings import NODE

# this only works if the raspberry pi SenseHat package is installed
sense = None
try:
    from sense_hat import SenseHat
    sense = SenseHat()
except ImportError:
    pass

DATABASE = "rpdemo"
SAMPLE_INTERVAL = 5.0
PING_GOOGLE_HOST = "google.com.au"

def ping(host):
    """
    ping the given host.
    returns the ping time in ms, or zero if ping fails for any reason
    """
    ping_time = 0.0
    try:
        # args:  -c1 - send one ping
        #        -w1 - timeout after 1 second
        output = subprocess.check_output(["ping", "-c1", "-w1", host])
        # if any pings got through the last line shows the ping times:
        #   rtt min/avg/max/mdev = 13.965/13.965/13.965/0.000 ms
        # we capture the avg time
        pattern = r".*rtt.* = .+/(.+)/.+/.+ ms"
        match = re.search(pattern, output)
        if match:
            ping_time = float(match.group(1))
            logging.debug("ping {0} -> {1} ms".format(host, ping_time))
        else:
            raise ValueError("failed to parse ping output", output)
    except subprocess.CalledProcessError:
        logging.debug("ping {0} failed".format(host))
        pass

    return ping_time

def get_sensehat_fields():
    fields = {
        "temperature": float(sense.get_temperature()),
        "humidity": float(sense.get_humidity()),
        "pressure": float(sense.get_pressure())
    }

    return fields

def get_net_fields():
    # we use ping with a 1 second timeout, which means if the host
    # is not answering this call may take up to 1 second to return
    ping_google = ping(PING_GOOGLE_HOST)

    fields = {
        "ping_google": ping_google
    }

    return fields

def build_point(measurement, fields):
    point = {
        "measurement": measurement,
        "fields": fields
    }
    return point

def build_points(samplers):
    """
    build a list of influx points by getting metric values from the samplers
    """
    points = []

    for name, sampler in samplers.items():
        samples = sampler.get_samples()
        if samples:
            points.append(build_point(name, samples))

    points.append(build_point("net", get_net_fields()))

    global sense
    if sense is not None:
        points.append(build_sensehat_point)

    return points

if __name__ == "__main__":

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG)

    influx = InfluxDBClient("localhost", 8086)

    influx.create_database(DATABASE)
    influx.switch_database(DATABASE)

    # the samplers gather the metrics we are logging
    samplers = {}
    samplers["system"] = SystemSampler()
    samplers["wemo"] = WemoSampler()

    # every point is tagged with the node. This is not necessary in the local DB
    # but this way it's the same schema as the central DB (CDS)
    tags = {"node": NODE}

    while True:
        start_timestamp = datetime.datetime.now()

        points = build_points(samplers)

        built_timestamp = datetime.datetime.now()
        logging.debug("built points in {0} ms".format((built_timestamp - start_timestamp).total_seconds()*1000))
        logging.debug("{0} {1}".format(tags, points))

        influx.write_points(points, tags=tags)
        wrote_timestamp = datetime.datetime.now()
        logging.debug("wrote points in {0} ms".format((wrote_timestamp-built_timestamp).total_seconds()*1000))

        # the time taken to build and write the data points
        cycle_time = (datetime.datetime.now() - start_timestamp).total_seconds()
        if cycle_time < SAMPLE_INTERVAL:
            sleep_time_sec = SAMPLE_INTERVAL - cycle_time
            logging.debug("sleeping for {0} seconds".format(sleep_time_sec))
            time.sleep(sleep_time_sec)
        else:
            logging.warn("cycle time {0} exceeded sample interval {1}".format(cycle_time, SAMPLE_INTERVAL))
