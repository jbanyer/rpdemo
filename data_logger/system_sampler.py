from procfs import Proc

class SystemSampler:

    def __init__(self):
        self.proc = Proc()
        self.sample_funcs = {
            "loadavg1": lambda: self.get_loadavg()[1],
            "loadavg5": lambda: self.get_loadavg()[5],
            "loadavg15": lambda: self.get_loadavg()[15]
        }

    def get_loadavg(self):
    	"""returns the 1,5,15 min system load average as eg {1: 0.0, 5: 0.0, 15: 0.0}"""
        # return just the 1,5,15 load average values
        return self.proc.loadavg['average']

    def get_sample(self, key, arg):
        try:
            func = self.sample_funcs[key]
            return func()
        except KeyError:
            raise ValueError("unknown key: {0}".format(key))
