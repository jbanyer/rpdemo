import time
from sense_hat import SenseHat
from influxdb import InfluxDBClient
import system_metrics as sysmet

DATABASE = 'rpdemo'

sense = SenseHat()

def build_system_point():
    loadavg = sysmet.get_loadavg()

    fields = {
        'loadavg1': loadavg[1]
    }

    point = {
        'measurement': 'system',
        'fields': fields
    }

    return point

def build_sensehat_point():
    fields = {
        'temp': float(sense.get_temperature()),
        'humidity': float(sense.get_humidity()),
        'pressure': float(sense.get_pressure())
    }

    point = {
        'measurement': 'sensehat',
        'fields': fields
    }

    return point

def build_points():
    points = [
        build_system_point(),
        build_sensehat_point()
    ]
    return points

if __name__ == '__main__':

    influx = InfluxDBClient('localhost', 8086)

    influx.create_database(DATABASE)
    influx.switch_database(DATABASE)

    while True:
        points = build_points()
        print points
        influx.write_points(points)
        time.sleep(1)
