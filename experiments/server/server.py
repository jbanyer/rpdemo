from flask import Flask, request, abort, jsonify
from sense_hat import SenseHat

app = Flask(__name__)

current_display = 'temp'
sensehat = SenseHat()

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/display', methods=['GET', 'PUT'])
def display():
    global current_display
    global sensehat
    if request.method == 'PUT':
        if not request.json:
            abort(400)
        if not 'item' in request.json:
            abort(400)
        item = request.json['item']
        current_display = item
        app.logger.info('current display now: {0}'.format(item))
        sensehat.show_message(item)

    return jsonify({'item':current_display})

if __name__ == '__main__':
    app.run(debug=True)

