import os
import requests
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@reservation-db:5432/reservation_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.Integer, nullable=False)
    check_in = db.Column(db.String(20), nullable=False)
    check_out = db.Column(db.String(20), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "Reservation service is running!"

def user_exists(user_id):
    user_service_url = os.getenv('USER_SERVICE_URL', 'http://user-service:5000/users')
    response = requests.get(f"{user_service_url}/{user_id}")
    return response.status_code == 200

def room_exists(room_id):
    room_service_url = os.getenv('ROOM_SERVICE_URL', 'http://room-service:5002/rooms')
    response = requests.get(f"{room_service_url}/{room_id}")
    return response.status_code == 200

@app.route('/reservations', methods=['POST'])
def add_reservation():
    data = request.get_json()
    if not data or 'user_id' not in data or 'room_id' not in data or 'check_in' not in data or 'check_out' not in data:
        return jsonify({"error": "Invalid input"}), 400

    if not user_exists(data['user_id']):
        return jsonify({"error": "User ID not found"}), 404
    if not room_exists(data['room_id']):
        return jsonify({"error": "Room ID not found"}), 404

    new_reservation = Reservation(
        user_id=data['user_id'],
        room_id=data['room_id'],
        check_in=data['check_in'],
        check_out=data['check_out']
    )
    db.session.add(new_reservation)
    db.session.commit()
    return jsonify({"message": "Reservation created successfully"}), 201

@app.route('/reservations', methods=['GET'])
def get_reservations():
    reservations = Reservation.query.all()
    reservation_list = [
        {
            "id": reservation.id,
            "user_id": reservation.user_id,
            "room_id": reservation.room_id,
            "check_in": reservation.check_in,
            "check_out": reservation.check_out
        }
        for reservation in reservations
    ]
    return jsonify(reservation_list), 200

@app.route('/reservations/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
    return jsonify({
        "id": reservation.id,
        "user_id": reservation.user_id,
        "room_id": reservation.room_id,
        "check_in": reservation.check_in,
        "check_out": reservation.check_out
    }), 200

@app.route('/reservations/<int:reservation_id>', methods=['PUT'])
def update_reservation(reservation_id):
    data = request.get_json()
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
    if 'check_in' in data:
        reservation.check_in = data['check_in']
    if 'check_out' in data:
        reservation.check_out = data['check_out']
    db.session.commit()
    return jsonify({"message": "Reservation updated successfully"}), 200

@app.route('/reservations/<int:reservation_id>', methods=['DELETE'])
def delete_reservation(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
    db.session.delete(reservation)
    db.session.commit()
    return jsonify({"message": "Reservation deleted successfully"}), 200

@app.route('/reservations/user/<int:user_id>', methods=['GET'])
def get_user_reservations(user_id):

    reservations = Reservation.query.filter_by(user_id=user_id).all()
    if not reservations:
        return jsonify({"message": "No reservations found for this user."}), 404
    reservation_list = [
        {
            "id": reservation.id,
            "room_id": reservation.room_id,
            "check_in": reservation.check_in,
            "check_out": reservation.check_out
        }
        for reservation in reservations
    ]
    return jsonify(reservation_list), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
