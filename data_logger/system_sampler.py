from procfs import Proc

class SystemSampler:

    def __init__(self):
        self.proc = Proc()

    def get_loadavg(self):
    	"""returns the 1,5,10 min system load average as eg {1: 0.0, 5: 0.0, 15: 0.0}"""
        # return just the 1,5,15 load average values
        return self.proc.loadavg['average']

    def get_samples(self):
        samples = {
            "loadavg1": self.get_loadavg()[1]
        }

        return samples
