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

    def get_samples(self):
        # TODO: do we need to run discovery periodically to discover/enabled new switches?
        switch_names = self.wemo_env.list_switches()
        samples = {}
        for switch_name in switch_names:
            switch = self.wemo_env.get_switch(switch_name)
            # is it on or off (1 or 0)?
            samples[switch_name+".state"] = switch.get_state()
            # only Insight Switches can report power, not the regular switches
            if hasattr(switch, "current_power"):
                # current_power seems to be in mW, convert to W
                samples[switch_name+".power"] = switch.current_power / 1000.0

        return samples
