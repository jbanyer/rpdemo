import logging
import re
import subprocess

PING_GOOGLE_HOST = "google.com.au"

def ping(host):
    """
    ping the given host.
    returns the ping time in ms, or zero if ping fails for any reason
    """
    ping_time = 0.0
    try:
        # args:  -c1 - send one ping
        #        -w1 - timeout after 1 second
        output = subprocess.check_output(["ping", "-c1", "-w1", host])
        # if any pings got through the last line shows the ping times:
        #   rtt min/avg/max/mdev = 13.965/13.965/13.965/0.000 ms
        # we capture the avg time
        pattern = r".*rtt.* = .+/(.+)/.+/.+ ms"
        match = re.search(pattern, output)
        if match:
            ping_time = float(match.group(1))
            logging.debug("ping {0} -> {1} ms".format(host, ping_time))
        else:
            raise ValueError("failed to parse ping output", output)
    except subprocess.CalledProcessError:
        logging.debug("ping {0} failed".format(host))
        pass

    return ping_time

class NetSampler:
    """Returns metrics for network access"""

    def __init__(self):
        pass

    def get_samples(self):
        # we use ping with a 1 second timeout, which means if the host
        # is not answering this call may take up to 1 second to return
        ping_google = ping(PING_GOOGLE_HOST)

        samples = {
            "ping_google": ping_google
        }

        return samples
