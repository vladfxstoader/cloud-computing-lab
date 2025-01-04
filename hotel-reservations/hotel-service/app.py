import os
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

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',
                                                  'postgresql://postgres:postgres@hotel-db:5432/hotel_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    facilities = db.Column(db.ARRAY(db.String), nullable=True)

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

tracer = initialize_tracer("hotel-service")
flask_tracer = FlaskTracing(tracer, True, app)

@app.route('/')
def index():
    return "Hotel service is running!"

@app.route('/hotels', methods=['POST'])
def create_hotel():
    span_ctx = tracer.extract(Format.HTTP_HEADERS, request.headers)
    with tracer.start_span('create_hotel', child_of=span_ctx) as span:
        span.set_tag('http.method', 'POST')
        span.set_tag('endpoint', '/hotels')

        data = request.get_json()
        if not data or 'name' not in data or 'location' not in data:
            span.log_kv({'error': 'Invalid input'})
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
    with tracer.start_span('get_hotels') as span:
        hotels = Hotel.query.all()
        hotel_list = [
            {"id": hotel.id, "name": hotel.name, "location": hotel.location, "facilities": hotel.facilities}
            for hotel in hotels
        ]
        span.log_kv({'hotels_count': len(hotel_list)})
        return jsonify(hotel_list), 200

@app.route('/hotels/<int:hotel_id>', methods=['GET'])
def get_hotel(hotel_id):
    with tracer.start_span('get_hotel') as span:
        span.set_tag('hotel_id', hotel_id)
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            span.log_kv({'error': 'Hotel not found'})
            return jsonify({"error": "Hotel not found"}), 404
        return jsonify({
            "id": hotel.id,
            "name": hotel.name,
            "location": hotel.location,
            "facilities": hotel.facilities
        }), 200

@app.route('/hotels/<int:hotel_id>', methods=['PUT'])
def update_hotel(hotel_id):
    with tracer.start_span('update_hotel') as span:
        span.set_tag('hotel_id', hotel_id)
        data = request.get_json()
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            span.log_kv({'error': 'Hotel not found'})
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
    with tracer.start_span('delete_hotel') as span:
        span.set_tag('hotel_id', hotel_id)
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            span.log_kv({'error': 'Hotel not found'})
            return jsonify({"error": "Hotel not found"}), 404
        db.session.delete(hotel)
        db.session.commit()
        return jsonify({"message": "Hotel deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
