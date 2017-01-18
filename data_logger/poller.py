import datetime
import logging
import random
import time
from sampler import Sampler
from Queue import Queue, Empty
from threading import Thread

SAMPLE_INTERVAL = 1.0
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
            logging.debug("{0} result: {1}".format(self, self.last_value))
        except Exception as e:
            self.last_value = None
            logging.debug("{0} error: {1}".format(self, e))
        self.poll_in_progress = False

    def init_next_poll_time(self, now):
        # for the initial poll, add a random delay up the interval to stagger the items
        delay = random.randint(0, self.interval)
        self.next_poll_time = now + datetime.timedelta(seconds=delay)

class PollingThread(Thread):
    def __init__(self, polling_queue, result_queue, sampler):
        super(PollingThread, self).__init__()
        self._polling_queue = polling_queue
        self.result_queue = result_queue
        self.sampler = sampler
        # polling threads should die immediately when the process ends
        self.daemon = True

    def run(self):
        logging.info("polling thread {0} started".format(self.ident))
        while True:
            item = self._polling_queue.get()
            logging.debug("thread {0} polling item {1}".format(self.ident, item.name))
            item.do_poll(self.sampler)
            if item.last_value is not None:
                self.result_queue.put(item)

class Poller:
    def __init__(self):
        self._sampler = Sampler()
        self._items = []
        self._threads = []
        self._polling_queue = Queue() # items that require polling by a polling thread
        self._result_queue = Queue()  # items that have just been polled by a polling thread
        self._start_polling_threads(POLLING_THREADS)

    def _start_polling_threads(self, num_threads):
        for i in range(num_threads):
            thread = PollingThread(self._polling_queue, self._result_queue, self._sampler)
            thread.start()
            self._threads.append(thread)

    def _init_items(self):
        now = datetime.datetime.now()
        for item in self._items:
            item.init_next_poll_time(now)

    def add_item(self, name, key, arg, interval):
        """
        add a new item to be polled
           name: eg "ping google.com.au"
           key: eg "net.ping"
           arg: eg "google.com.au" (optional, use depends on key)
           interval: eg 5.0 (seconds)
        """
        self._items.append(PollItem(name, key, arg, interval))

    def run(self, results_callback):
        """
        Run the polling main loop, polling items as per their polling interval.
        Results are collected once per second and provided via results_callback(items),
        where items is a list of PollItems.
        This method does not return.
        """
        self._init_items()

        while True:
            start_timestamp = datetime.datetime.now()

            # enque the due items for polling by the threads
            self._dispatch_due_items()

            # Wait a short while for fast poll results to come in. It doesn't matter if slow ones are not
            # complete after this wait - we'll check for them next time around.
            time.sleep(0.1)

            # collect any results (PollItems) that are ready
            result_items = self._collect_poll_results()

            if result_items:
                results_callback(result_items)

            cycle_time = (datetime.datetime.now() - start_timestamp).total_seconds()
            if cycle_time < SAMPLE_INTERVAL:
                sleep_time_sec = SAMPLE_INTERVAL - cycle_time
                logging.debug("sleeping for {0} seconds".format(sleep_time_sec))
                time.sleep(sleep_time_sec)
            else:
                logging.warn("cycle time {0} exceeded sample interval {1}".format(cycle_time, SAMPLE_INTERVAL))

    def _dispatch_due_items(self):
        """
        enqueue any due poll items for processing by the polling threads
        """
        now = datetime.datetime.now()

        # an item is polled if the current time is within 0.5s of the due poll time.
        # this avoids failing to poll every second cycle
        tolerance = datetime.timedelta(seconds=0.5)

        # find the items that are now due to be polled
        items_due = [i for i in self._items if i.needs_poll(now, tolerance)]

        # add the due items to the polling queue
        logging.debug("adding {0} items to polling queue (size was {1})".format(len(items_due), self._polling_queue.qsize()))
        for item in items_due:
            item.poll_in_progress = True
            self._polling_queue.put(item)

    def _collect_poll_results(self):
        """
        return (and remove) any currently available poll results (a list of PollItems)
        does not block or wait for any results
        """
        items = []
        while True:
            try:
                items.append(self._result_queue.get_nowait())
            except Empty:
                break
        return items
