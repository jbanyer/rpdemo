from influxdb import InfluxDBClient
from flask import Flask, request, abort, jsonify

DATABASE = "cds"

# the influx database connection
db = None

@app.route("/write", methods=["PUT"])
def display():
    if not request.json:
        abort(400)

    if not "item" in request.json:
        abort(400)
        item = request.json["item"]
        current_display = item
        app.logger.info("current display now: {0}".format(item))
        sensehat.show_message(item)

    return jsonify({"item":current_display})

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    global db
    db = InfluxDBClient("localhost", 8086)

    db.create_database(DATABASE)
    db.switch_database(DATABASE)

    app.run(debug=True)
