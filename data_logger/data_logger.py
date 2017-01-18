from influxdb import InfluxDBClient
import logging
import json
from poller import Poller

CONFIG_FILENAME = "data_logger_config.json"
DEFAULT_DATABASE = "rpdemo"
DEFAULT_NUM_POLLING_THREADS = 4

class DataLogger:
    def __init__(self):
        self._influx = None
        self._poller = Poller()

        self._database_name = DEFAULT_DATABASE
        self._num_polling_threads = DEFAULT_NUM_POLLING_THREADS

    def load_config(self, filename):
        config_str = open(filename).read()
        logging.info(config_str)
        config = json.loads(config_str)

        self._database_name = config["database"]
        self._num_polling_threads = config.get("polling_threads", DEFAULT_NUM_POLLING_THREADS)
        self._poller.set_items_config(config["items"])

    def get_config(self):
        config = {
            "database": self._database_name,
            "polling_threads": self._num_polling_threads,
            "items": self._poller.get_items_config()
        }
        return config

    def get_poll_items(self):
        return self._poller.get_poll_items()

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
        self._influx = InfluxDBClient("localhost", 8086)
        self._influx.create_database(self._database_name)
        self._influx.switch_database(self._database_name)

        self._poller.run(self._num_polling_threads, self._process_results)

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
    data_logger.load_config(CONFIG_FILENAME)
    data_logger.run()
