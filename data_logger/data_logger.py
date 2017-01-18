import datetime
from influxdb import InfluxDBClient
import logging
from system_sampler import SystemSampler
from wemo_sampler import WemoSampler
from sense_hat_sampler import SenseHatSampler
from net_sampler import NetSampler
from settings import NODE
from poller import Poller

DATABASE = "rpdemo"

class DataLogger:
    def __init__(self):
        self._influx = InfluxDBClient("localhost", 8086)
        self._influx.create_database(DATABASE)
        self._influx.switch_database(DATABASE)

        self._poller = Poller()

    def create_test_items(self):
        self._poller.add_item("loadavg1 1s", "system.loadavg1", None, 1)
        self._poller.add_item("loadavg1 5s", "system.loadavg1", None, 5)
        self._poller.add_item("loadavg1 60s", "system.loadavg1", None, 60)

        self._poller.add_item("ping google.com.au", "net.ping", "google.com.au", 1)
        self._poller.add_item("ping google.com", "net.ping", "google.com", 1)
        self._poller.add_item("ping www.microsoft.com", "net.ping", "www.microsoft.com", 1)
        self._poller.add_item("ping www.tesla.co", "net.ping", "www.tesla.co", 1)

        self._poller.add_item("switch1 power", "wemo.power", "switch1", 1)
        self._poller.add_item("switch1 state", "wemo.state", "switch1", 1)

        self._poller.add_item("sensehat temperature", "sensehat.temperature", None, 10)
        self._poller.add_item("sensehat humidity", "sensehat.humidity", None, 10)
        self._poller.add_item("sensehat pressure", "sensehat.pressure", None, 10)

    def run(self):
        self._poller.run(self._process_results)

    def _build_points(self, items):
        """build a list of influx data points from the given list of PollItems"""
        fields = {}
        for item in items:
            fields[item.name] = item.last_value

        point = {
            "measurement": "rpdemo",
            "fields": fields
        }

        return [point]

    def _process_results(self, items):
        # build influx points from the results and write them to influx DB
        points = self._build_points(items)

        logging.debug("{0}".format(points))

        self._influx.write_points(points)


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.DEBUG)
    data_logger = DataLogger()
    data_logger.create_test_items()
    data_logger.run()
