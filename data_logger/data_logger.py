import datetime
import time
from influxdb import InfluxDBClient
import logging
from system_sampler import SystemSampler
from wemo_sampler import WemoSampler
from sense_hat_sampler import SenseHatSampler
from net_sampler import NetSampler
from settings import NODE

DATABASE = "rpdemo"
SAMPLE_INTERVAL = 5.0

def build_points(samplers):
    """build a list of influx points by getting metric values from the samplers"""
    points = []

    for name, sampler in samplers.items():
        samples = sampler.get_samples()
        if samples:
            point = {
                "measurement": name,
                "fields": samples
            }
            points.append(point)

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
    samplers["net"] = NetSampler()
    samplers["sensehat"] = SenseHatSampler()

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
