import datetime
import time
from influxdb import InfluxDBClient
import logging
from system_sampler import SystemSampler
from wemo_sampler import WemoSampler
from sense_hat_sampler import SenseHatSampler
from net_sampler import NetSampler
from settings import NODE
from poller import Poller

DATABASE = "rpdemo"
SAMPLE_INTERVAL = 1.0

def build_points(items):
    """build a list of influx data points from the given list of PollItems"""
    fields = {}
    for item in items:
        fields[item.name] = item.last_value

    point = {
        "measurement": "rpdemo",
        "fields": fields
    }

    return [point]

if __name__ == "__main__":

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG)

    influx = InfluxDBClient("localhost", 8086)

    influx.create_database(DATABASE)
    influx.switch_database(DATABASE)

    poller = Poller()

    # create some example items to poll
    poller.create_test_items()

    poller.init()

    # every point is tagged with the node. This is not necessary in the local DB
    # but this way it's the same schema as the central DB (CDS)
    tags = {"node": NODE}

    while True:
        start_timestamp = datetime.datetime.now()

        # enque the due items for polling by the threads
        poller.poll_due_items_async()

        # Wait a short while for fast poll results to come in. It doesn't matter if slow ones are not
        # complete after this wait - we'll check for them next time around.
        time.sleep(0.1)

        # collect any results (PollItems) that are ready
        result_items = poller.collect_poll_results()

        if result_items:
            # build influx points from the results and write them to influx DB
            points = build_points(result_items)

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
