import time
from sense_hat import SenseHat
from influxdb import InfluxDBClient

DATABASE = 'rpdemo'

sense = SenseHat()
influx = InfluxDBClient('localhost', 8086)

influx.create_database(DATABASE)
influx.switch_database(DATABASE)

points = [
    {
        "measurement": "temp",
        "fields": {
            "value": -99
        }
    }
]

while True:
    temp = sense.get_temperature()
    points[0]['fields']['value'] = temp
    print points
    influx.write_points(points)
    time.sleep(1)
