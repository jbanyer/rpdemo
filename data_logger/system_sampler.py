from procfs import Proc

class SystemSampler:

    def __init__(self):
        self.proc = Proc()
        self.sample_funcs = {
            "loadavg1": lambda: self.get_loadavg()[1]
        }

    def get_loadavg(self):
    	"""returns the 1,5,10 min system load average as eg {1: 0.0, 5: 0.0, 15: 0.0}"""
        # return just the 1,5,15 load average values
        return self.proc.loadavg['average']

    def get_sample(self, name, arg):
        try:
            func = self.sample_funcs[name]
            return func()
        except KeyError:
            raise ValueError("system sampler - unknown name: {0}".format(name))

    def get_samples(self):
        samples = {
            "loadavg1": self.get_loadavg()[1]
        }

        return samples
