from net_sampler import NetSampler
from sense_hat_sampler import SenseHatSampler
from system_sampler import SystemSampler
from wemo_sampler import WemoSampler

class Sampler:

    def __init__(self):
        self.samplers = {
            "net": NetSampler(),
            "sensehat": SenseHatSampler(),
            "system": SystemSampler(),
            "wemo": WemoSampler()
        }

    def get_sample(self, key, arg):
        """
        return a sample for the given key and (optional) arg. Examples:
           |-----------------------|------------------------|
           | key                   | arg                    |
           |-----------------------+------------------------|
           | net.ping              | google.com.au          |
           | sensehat.temperature  |                        |
           | system.loadavg1       |                        |
           | wemo.power            | switch1                |
           |-----------------------|------------------------|
        """
        sampler_name, subkey = key.split(".")
        return self.samplers[sampler_name].get_sample(subkey, arg)
