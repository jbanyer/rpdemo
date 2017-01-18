import logging

class SenseHatSampler:

    def __init__(self):
        # this only works if the raspberry pi sense_hat package is installed
        self.sense = None
        try:
            from sense_hat import SenseHat
            self.sense = SenseHat()

            self.sample_funcs = {
                "temperature": lambda: float(self.sense.get_temperature()),
                "humidity": lambda: float(self.sense.get_humidity()),
                "pressure": lambda: float(self.sense.get_pressure())
            }
        except ImportError:
            logging.info("sense_hat package not found")

    def available(self):
        return self.sense is not None

    def get_sample(self, key, args):
        if self.sense is None:
            raise ValueError("sense_hat is not available")

        try:
            func = self.sample_funcs[key]
            return func()
        except KeyError:
            raise ValueError("sense_hat sampler: unknown key: {0}".format(key))

    def get_samples(self):
        if self.sense:
            samples = {
                "temperature": float(self.sense.get_temperature()),
                "humidity": float(self.sense.get_humidity()),
                "pressure": float(self.sense.get_pressure())
            }
            return samples
        else:
            return None
