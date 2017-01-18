import logging
from threading import Thread
from data_logger import DataLogger
from poller import ItemExistsError
from flask import Flask, request, abort, jsonify, make_response, url_for

# Configure the logging before creating the Flask app otherwise it will
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

app = Flask(__name__)

data_logger = DataLogger()

def item_as_dict(poll_item):
    """return a dict version of the given PollItem"""
    # simply return all the fields of the PollItem, plus a url field
    item_dict = poll_item.__dict__
    item_dict["url"] = url_for("get_item", name=poll_item.name, _external=True)
    return item_dict

def item_valid(item):
    return "name" in item and "key" in item and "interval" in item

def make_error_response(error_message, error_code):
    return make_response(jsonify({"error": error_message}), error_code)


@app.route("/items/", methods=["GET"])
def get_items():
    """Return a list of all the poll items"""
    global data_logger
    poll_items = data_logger.get_items()
    return jsonify([item_as_dict(item) for item in poll_items])

@app.route("/items/<name>", methods=["GET"])
def get_item(name):
    """return the item with the given name"""
    global data_logger
    try:
        poll_item = data_logger.get_item(name)
        return jsonify(item_as_dict(poll_item))
    except KeyError as e:
        return make_error_response(e.message, 404)

@app.route("/items/", methods=["POST"])
def add_item():
    """Add a new poll item given its required fields"""
    if not request.json:
        abort(make_error_response("request must be JSON", 400))

    item = request.json
    logging.info(item)
    if not item_valid(item):
        abort(make_error_response("incomplete item", 400))

    global data_logger
    try:
        data_logger.add_item(**item)
    except ItemExistsError as e:
        abort(make_error_response(e.message, 422))

    return jsonify(item), 201

@app.route("/items/<name>", methods=["DELETE"])
def delete_item(name):
    """delete the item with the given name"""
    global data_logger
    try:
        data_logger.delete_item(name)
        return jsonify({"result": True})
    except KeyError as e:
        return make_error_response(e.message, 404)


if __name__ == "__main__":
    data_logger.load_config("data_logger_config.json")

    # run the data logger in a thread, concurrently with the Flask service app
    data_logger_thread = Thread(target=data_logger.run)
    # We haven't implemented a way to stop the data logger yet so make it
    # a daemon thread so it quits immediately when the main thread stops.
    data_logger_thread.daemon = True
    data_logger_thread.start()

    # run the flask app in the main thread
    app.run(debug=True)
