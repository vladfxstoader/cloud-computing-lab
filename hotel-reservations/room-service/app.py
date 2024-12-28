from flask import Flask, request, jsonify

app = Flask(__name__)

rooms = []

@app.route('/add_room', methods=['POST'])
def add_room():
    data = request.get_json()
    room = {
        'id': len(rooms) + 1,
        'hotel_id': data['hotel_id'],
        'type': data['type'],
        'price': data['price'],
        'availability': data.get('availability', True)
    }
    rooms.append(room)
    return jsonify(room), 201

@app.route('/rooms', methods=['GET'])
def get_rooms():
    return jsonify(rooms), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
