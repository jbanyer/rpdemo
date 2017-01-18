from ouimeaux.environment import Environment
import logging

class WemoSampler:

    def __init__(self):
        self.wemo_env = Environment()
        self.wemo_env.start()
        self.discover()

    def discover(self):
        logging.info("searching for WeMo devices")
        self.wemo_env.discover(seconds=1)
        logging.info("WeMo devices found: {0}".format(self.wemo_env.devices))

    def get_switch(self, switch_name):
        return self.wemo_env.get_switch(switch_name)

    def get_sample(self, key, arg):
        if key == "power":
            if not arg:
                raise ValueError("wemo.power requires arg (switch name)")
            switch = self.get_switch(arg)
            # current_power seems to be in mW, convert to W
            return switch.current_power / 1000.0
        elif key == "state":
            if not arg:
                raise ValueError("wemo.state requires arg (switch name)")
            switch = self.get_switch(arg)
            return switch.get_state()
        else:
            raise ValueError("unknown key: {0}".format(key))
