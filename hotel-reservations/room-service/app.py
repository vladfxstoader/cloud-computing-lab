import os
import requests
from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Counter, generate_latest
from flask_opentracing import FlaskTracing
from jaeger_client import Config
from opentracing.propagation import Format

app = Flask(__name__)

http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])

@app.before_request
def before_request():
    http_requests_total.labels(request.method, request.endpoint).inc()

@app.route('/metrics', methods=['GET'])
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@room-db:5432/room_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, default=True)

with app.app_context():
    db.create_all()

def initialize_tracer(service_name):
    config = Config(
        config={
            'sampler': {'type': 'const', 'param': 1},
            'logging': True,
            'local_agent': {'reporting_host': 'jaeger', 'reporting_port': 6831},
        },
        service_name=service_name,
    )
    return config.initialize_tracer()

tracer = initialize_tracer("room-service")
flask_tracer = FlaskTracing(tracer, True, app)

@app.route('/')
def index():
    return "Room service is running!"

def hotel_exists(hotel_id):
    span_ctx = tracer.extract(Format.HTTP_HEADERS, request.headers)
    with tracer.start_span('check_hotel_exists', child_of=span_ctx) as span:
        hotel_service_url = os.getenv('HOTEL_SERVICE_URL', 'http://hotel-service:5001/hotels')
        span.set_tag('hotel_service_url', hotel_service_url)
        span.set_tag('hotel_id', hotel_id)

        response = requests.get(f"{hotel_service_url}/{hotel_id}")
        span.log_kv({'response_status_code': response.status_code})
        return response.status_code == 200

@app.route('/rooms', methods=['POST'])
def add_room():
    span_ctx = tracer.extract(Format.HTTP_HEADERS, request.headers)
    with tracer.start_span('add_room', child_of=span_ctx) as span:
        data = request.get_json()
        span.log_kv({'room_data': data})

        if not data or 'hotel_id' not in data or 'type' not in data or 'price' not in data:
            span.log_kv({'error': 'Invalid input'})
            return jsonify({"error": "Invalid input"}), 400

        if not hotel_exists(data['hotel_id']):
            span.log_kv({'error': 'Hotel with given id not found'})
            return jsonify({"error": "Hotel with given id not found!"}), 404

        new_room = Room(
            hotel_id=data['hotel_id'],
            type=data['type'],
            price=data['price'],
            availability=data.get('availability', True)
        )
        db.session.add(new_room)
        db.session.commit()
        span.log_kv({'room_id': new_room.id})
        return jsonify({"message": "Room created successfully"}), 201

@app.route('/rooms', methods=['GET'])
def get_rooms():
    with tracer.start_span('get_rooms') as span:
        rooms = Room.query.all()
        room_list = [
            {
                "id": room.id,
                "hotel_id": room.hotel_id,
                "type": room.type,
                "price": room.price,
                "availability": room.availability
            }
            for room in rooms
        ]
        span.log_kv({'rooms_count': len(room_list)})
        return jsonify(room_list), 200

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    with tracer.start_span('get_room') as span:
        span.set_tag('room_id', room_id)
        room = Room.query.get(room_id)
        if not room:
            span.log_kv({'error': 'Room not found'})
            return jsonify({"error": "Room not found"}), 404
        return jsonify({
            "id": room.id,
            "hotel_id": room.hotel_id,
            "type": room.type,
            "price": room.price,
            "availability": room.availability
        }), 200

@app.route('/rooms/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    with tracer.start_span('update_room') as span:
        span.set_tag('room_id', room_id)
        data = request.get_json()
        span.log_kv({'update_data': data})

        room = Room.query.get(room_id)
        if not room:
            span.log_kv({'error': 'Room not found'})
            return jsonify({"error": "Room not found"}), 404
        if 'type' in data:
            room.type = data['type']
        if 'price' in data:
            room.price = data['price']
        if 'availability' in data:
            room.availability = data['availability']
        db.session.commit()
        return jsonify({"message": "Room updated successfully"}), 200

@app.route('/rooms/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    with tracer.start_span('delete_room') as span:
        span.set_tag('room_id', room_id)
        room = Room.query.get(room_id)
        if not room:
            span.log_kv({'error': 'Room not found'})
            return jsonify({"error": "Room not found"}), 404
        db.session.delete(room)
        db.session.commit()
        return jsonify({"message": "Room deleted successfully"}), 200

@app.route('/rooms/hotel/<int:hotel_id>', methods=['GET'])
def get_rooms_by_hotel(hotel_id):
    with tracer.start_span('get_rooms_by_hotel') as span:
        span.set_tag('hotel_id', hotel_id)
        rooms = Room.query.filter_by(hotel_id=hotel_id).all()
        if not rooms:
            span.log_kv({'error': 'No rooms found for the given hotel'})
            return jsonify({"error": "No rooms found for the given hotel"}), 404
        room_list = [
            {
                "id": room.id,
                "type": room.type,
                "price": room.price,
                "availability": room.availability
            }
            for room in rooms
        ]
        span.log_kv({'rooms_count': len(room_list)})
        return jsonify(room_list), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
