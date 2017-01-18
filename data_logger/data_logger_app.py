import logging
from threading import Thread
from data_logger import DataLogger
from flask import Flask, request, abort, jsonify, make_response

# Configure the logging before creating the Flask app otherwise it will
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

app = Flask(__name__)

data_logger = DataLogger()

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'bad request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Not found"}), 404)

@app.route("/items", methods=["GET"])
def list_items():
    global data_logger
    poll_items = data_logger.get_poll_items()
    return jsonify([item.__dict__ for item in poll_items])

@app.route("/items", methods=["POST"])
def add_item():
    global data_logger
    if not request.json:
        abort(400)
    abort(400)

def data_logger_main():
    global data_logger
    data_logger.run()

if __name__ == "__main__":
    data_logger.load_config("data_logger_config.json")

    # run the data logger in a thread, concurrently with the Flask service app
    data_logger_thread = Thread(target=data_logger.run)
    # We haven't implemented a way to stop the data logger yet so make it
    # a daemon thread so it quits abruptly when the main thread stops.
    data_logger_thread.daemon = True
    data_logger_thread.start()

    # run the flask app in the main thread
    app.run(debug=True)
