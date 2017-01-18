from ouimeaux.environment import Environment
import logging

wemo_env = Environment()
wemo_env.start()
wemo_env.discover(seconds=3)

def get_samples():
    global wemo_env

    switch_names = wemo_env.list_switches()
    # TODO: do we need to run discovery periodically to discover/enabled new switches?
    if not switch_names:
        logging.debug("there are no wemo switches")
        return

    samples = {}
    for switch_name in wemo_env.list_switches():
        switch = wemo_env.get_switch(switch_name)
        # is it on or off (1 or 0)?
        samples[switch_name+".state"] = switch.get_state()
        # only Insight Switches can report power, not the regular switches
        if hasattr(switch, "current_power"):
            # current_power seems to be in mW, convert to W
            samples[switch_name+".power"] = switch.current_power / 1000.0

    return samples
