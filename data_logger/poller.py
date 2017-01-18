import datetime
import logging
import random
from system_sampler import SystemSampler
from Queue import Queue, Empty
from threading import Thread

POLLING_THREADS = 4

class PollItem:
    def __init__(self, name, sampler, key, args, interval):
        self.name = name
        self.sampler = sampler
        self.key = key
        self.args = args
        self.interval = interval
        self.last_value = None
        self.next_poll_time = None
        self.poll_in_progress = False

    def do_poll(self):
        self.last_value = self.sampler.get_sample(self.key, self.args)

    def update_next_poll_time(self, now):
        if self.next_poll_time is None:
            # for the initial poll, add a random delay up the interval to stagger the items
            delay = random.randint(0, self.interval)
            self.next_poll_time = now + datetime.timedelta(seconds=delay)
        else:
            self.next_poll_time = max(self.next_poll_time + datetime.timedelta(seconds=self.interval),
                now + datetime.timedelta(seconds=1))
        logging.debug("item {0} next poll time {1}".format(self.name, self.next_poll_time))


class PollingThread(Thread):
    def __init__(self, polling_queue, result_queue):
        super(PollingThread, self).__init__()
        self.polling_queue = polling_queue
        self.result_queue = result_queue
        # polling threads should die immediately when the process ends
        self.daemon = True

    def run(self):
        logging.info("polling thread {0} started".format(self.ident))
        while True:
            item = self.polling_queue.get()
            logging.debug("thread {0} polling item {1}".format(self.ident, item.name))
            item.do_poll()
            self.result_queue.put(item)

class Poller:
    def __init__(self):
        self.items = []
        self.threads = []
        self.waiting_queue = []          # items waiting for the next poll time to be due
        self.polling_queue = Queue()     # items ready and waiting for a polling thread
        self.result_queue = Queue()      # items that have just been polled by a polling thread

    def start_polling_threads(self, num_threads):
        for i in range(num_threads):
            thread = PollingThread(self.polling_queue, self.result_queue)
            thread.start()
            self.threads.append(thread)

    def create_test_items(self):
        system_sampler = SystemSampler()

        self.items.append(PollItem("loadavg1 1s", system_sampler, "loadavg1", None, 1))
        self.items.append(PollItem("loadavg1 5s", system_sampler, "loadavg1", None, 5))
        self.items.append(PollItem("loadavg1 60s", system_sampler, "loadavg1", None, 60))

    def init(self):
        self.start_polling_threads(POLLING_THREADS)
        now = datetime.datetime.now()
        for item in self.items:
            item.update_next_poll_time(now)
            self.waiting_queue.append(item)

    def poll_due_items_async(self):
        now = datetime.datetime.now()

        # find the waiting items that are now due to be polled and remove them from the waiting queue
        items_due = []
        new_waiting_queue = []
        for item in self.waiting_queue:
            if item.next_poll_time <= now:
                items_due.append(item)
            else:
                new_waiting_queue.append(item)
        self.waiting_queue = new_waiting_queue

        # add the due items to the polling queue
        logging.debug("adding {0} items to polling queue".format(len(items_due)))
        for item in items_due:
            item.update_next_poll_time(now)
            self.polling_queue.put(item)

    def collect_poll_results(self):
        """
        return any currently available poll results (a list of PollItems)
        move the returned items to the waiting queue so they can be polled again
        does not block or wait for any results
        """
        items = []
        while True:
            try:
                items.append(self.result_queue.get_nowait())
            except Empty:
                break
        self.waiting_queue.extend(items)
        return items
