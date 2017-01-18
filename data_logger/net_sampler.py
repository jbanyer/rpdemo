import logging
import re
import subprocess

def ping(host):
    """
    ping the given host.
    returns the ping time in ms, or zero if ping fails for any reason
    """
    ping_time = 0.0
    try:
        # ping args:  -c1 - send one ping
        #             -w1 - timeout after 1 second
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

    def get_sample(self, key, arg):
        if key == "ping":
            if not arg:
                raise ValueError("ping requires host arg")
            host = arg
            return ping(host)
        else:
            raise ValueError("NetSampler unknown key: {0}".format(key))
