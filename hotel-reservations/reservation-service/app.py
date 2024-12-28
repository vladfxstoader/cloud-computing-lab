from flask import Flask, request, jsonify
app = Flask(__name__)

reservations = []

@app.route('/reserve', methods=['POST'])
def reserve():
    data = request.get_json()
    reservation = {
        'id': len(reservations) + 1,
        'user_id': data['user_id'],
        'room_id': data['room_id'],
        'check_in': data['check_in'],
        'check_out': data['check_out']
    }
    reservations.append(reservation)
    return jsonify(reservation), 201

@app.route('/reservations', methods=['GET'])
def get_reservations():
    return jsonify(reservations), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)