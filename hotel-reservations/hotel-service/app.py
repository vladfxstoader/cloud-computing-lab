import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@hotel-db:5432/hotel_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    facilities = db.Column(db.ARRAY(db.String), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "Hotel service is running!"

@app.route('/hotels', methods=['POST'])
def create_hotel():
    data = request.get_json()
    if not data or 'name' not in data or 'location' not in data:
        return jsonify({"error": "Invalid input"}), 400

    new_hotel = Hotel(
        name=data['name'],
        location=data['location'],
        facilities=data.get('facilities', [])
    )
    db.session.add(new_hotel)
    db.session.commit()
    return jsonify({"message": "Hotel created successfully"}), 201

@app.route('/hotels', methods=['GET'])
def get_hotels():
    hotels = Hotel.query.all()
    hotel_list = [
        {"id": hotel.id, "name": hotel.name, "location": hotel.location, "facilities": hotel.facilities}
        for hotel in hotels
    ]
    return jsonify(hotel_list), 200

@app.route('/hotels/<int:hotel_id>', methods=['GET'])
def get_hotel(hotel_id):
    hotel = Hotel.query.get(hotel_id)
    if not hotel:
        return jsonify({"error": "Hotel not found"}), 404
    return jsonify({
        "id": hotel.id,
        "name": hotel.name,
        "location": hotel.location,
        "facilities": hotel.facilities
    }), 200

@app.route('/hotels/<int:hotel_id>', methods=['PUT'])
def update_hotel(hotel_id):
    data = request.get_json()
    hotel = Hotel.query.get(hotel_id)
    if not hotel:
        return jsonify({"error": "Hotel not found"}), 404
    if 'name' in data:
        hotel.name = data['name']
    if 'location' in data:
        hotel.location = data['location']
    if 'facilities' in data:
        hotel.facilities = data['facilities']
    db.session.commit()
    return jsonify({"message": "Hotel updated successfully"}), 200

@app.route('/hotels/<int:hotel_id>', methods=['DELETE'])
def delete_hotel(hotel_id):
    hotel = Hotel.query.get(hotel_id)
    if not hotel:
        return jsonify({"error": "Hotel not found"}), 404
    db.session.delete(hotel)
    db.session.commit()
    return jsonify({"message": "Hotel deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
