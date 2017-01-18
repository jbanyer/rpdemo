import datetime
import logging
import random
from sampler import Sampler
from Queue import Queue, Empty
from threading import Thread

POLLING_THREADS = 4

class PollItem:
    def __init__(self, name, key, arg, interval):
        self.name = name
        self.key = key
        self.arg = arg
        self.interval = interval
        self.last_value = None
        self.next_poll_time = None
        self.poll_in_progress = False

    def __str__(self):
        return "{0} ({1}[{2}])".format(self.name, self.key, self.arg)

    def needs_poll(self, now, tolerance):
        return not self.poll_in_progress and (now - self.next_poll_time) > -tolerance

    def do_poll(self, sampler):
        self.next_poll_time = datetime.datetime.now() + datetime.timedelta(seconds=self.interval)
        try:
            self.last_value = sampler.get_sample(self.key, self.arg)
        except Exception as e:
            logging.debug("{0} error: {1}".format(self, e))
        self.poll_in_progress = False

    def init_next_poll_time(self, now):
        # for the initial poll, add a random delay up the interval to stagger the items
        delay = random.randint(0, self.interval)
        self.next_poll_time = now + datetime.timedelta(seconds=delay)

class PollingThread(Thread):
    def __init__(self, polling_queue, result_queue, sampler):
        super(PollingThread, self).__init__()
        self.polling_queue = polling_queue
        self.result_queue = result_queue
        self.sampler = sampler
        # polling threads should die immediately when the process ends
        self.daemon = True

    def run(self):
        logging.info("polling thread {0} started".format(self.ident))
        while True:
            item = self.polling_queue.get()
            logging.debug("thread {0} polling item {1}".format(self.ident, item.name))
            item.do_poll(self.sampler)
            self.result_queue.put(item)

class Poller:
    def __init__(self):
        self.sampler = Sampler()
        self.items = []
        self.threads = []
        self.polling_queue = Queue() # items that require polling by a polling thread
        self.result_queue = Queue()  # items that have just been polled by a polling thread

    def start_polling_threads(self, num_threads):
        for i in range(num_threads):
            thread = PollingThread(self.polling_queue, self.result_queue, self.sampler)
            thread.start()
            self.threads.append(thread)

    def create_test_items(self):
        self.items.append(PollItem("loadavg1 1s", "system.loadavg1", None, 1))
        self.items.append(PollItem("loadavg1 5s", "system.loadavg1", None, 5))
        self.items.append(PollItem("loadavg1 60s", "system.loadavg1", None, 60))

        self.items.append(PollItem("ping google.com.au", "net.ping", "google.com.au", 1))
        self.items.append(PollItem("ping google.com", "net.ping", "google.com", 1))
        self.items.append(PollItem("ping www.microsoft.com", "net.ping", "www.microsoft.com", 1))
        self.items.append(PollItem("ping www.tesla.co", "net.ping", "www.tesla.co", 1))

        self.items.append(PollItem("switch1 power", "wemo.power", "switch1", 1))
        self.items.append(PollItem("switch1 state", "wemo.state", "switch1", 1))

        self.items.append(PollItem("sensehat temperature", "sensehat.temperature", None, 10))
        self.items.append(PollItem("sensehat humidity", "sensehat.humidity", None, 10))
        self.items.append(PollItem("sensehat pressure", "sensehat.pressure", None, 10))

    def init(self):
        self.start_polling_threads(POLLING_THREADS)
        now = datetime.datetime.now()
        for item in self.items:
            item.init_next_poll_time(now)

    def poll_due_items_async(self):
        now = datetime.datetime.now()

        # an item is polled if the current time is within 0.5s of the due poll time.
        # this avoids failing to poll every second cycle
        tolerance = datetime.timedelta(seconds=0.5)

        # find the items that are now due to be polled
        items_due = [i for i in self.items if i.needs_poll(now, tolerance)]

        # add the due items to the polling queue
        logging.debug("adding {0} items to polling queue (size {1})".format(len(items_due), self.polling_queue.qsize()))
        for item in items_due:
            item.poll_in_progress = True
            self.polling_queue.put(item)

    def collect_poll_results(self):
        """
        return (and remove) any currently available poll results (a list of PollItems)
        does not block or wait for any results
        """
        items = []
        while True:
            try:
                items.append(self.result_queue.get_nowait())
            except Empty:
                break
        return items
