# rpdemo

This small project implements a data logger in Python, with the following attributes:

 * data is logged to [InfluxDB](https://www.influxdata.com/)
 * any number of metrics (poll items) may be logged
 * each poll item may have a different poll interval
 * minimum poll interval is 1 second
 * a simple REST API is provided to manage poll items (add, delete, show items)
 * data logger is configured using JSON

It is intended for use on a Raspberry Pi but should run on any Linux platform.

## usage

Install InfluxDB.

$ python data_logger_app.py

See data_logger_config.json for configuration.

WARNING - Flask runs in debug mode for now.


## Supported items

   | key                   | arg                    |
   | --------------------- | ---------------------- |
   | net.ping              | google.com.au          |
   | sensehat.temperature  |                        |
   | sensehat.humidity     |                        |
   | sensehat.pressure     |                        |
   | system.loadavg1       |                        |
   | system.loadavg5       |                        |
   | system.loadavg15      |                        |
   | wemo.power            | switch1                |
   | wemo.state            | switch1                |


## Design notes

 * The data logger is a multi-threaded Python process. This allows many items to be polled concurrently,
   in particular those that require network access eg net.ping and wemo.
 * Flask is used to implement the REST API
 * WeMo devices are accessed using [ouimeaux](http://ouimeaux.readthedocs.io/en/latest/readme.html)
 * SenseHat items only available on RaspberryPi with SenseHat hardware


## TODO and Ideas

 * review the thread safety, especially when adding/deleting items from the REST API
 * configuration to control the logging (ie level, to file instead of stdout etc)
 * add internal metrics for monitoring the polling thread performance, ie is it overloaded?
 * WeMo: scan for new devices periodically
 * create a cloud-based database and syncronise the local data to the cloud?

