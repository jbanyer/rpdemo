import logging

class SenseHatSampler:

    def __init__(self):
        # this only works if the raspberry pi sense_hat package is installed
        self.sense = None
        try:
            from sense_hat import SenseHat
            self.sense = SenseHat()
        except ImportError:
            logging.info("sense_hat package not found")
            pass

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
