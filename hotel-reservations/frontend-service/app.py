from flask import Flask, render_template, request, jsonify, redirect
import requests
import os

app = Flask(__name__)

HOTEL_BACKEND_URL = os.getenv('HOTEL_BACKEND_URL', 'http://hotel-service:5001')
ROOM_BACKEND_URL = os.getenv('ROOM_BACKEND_URL', 'http://room-service:5002')
RESERVATION_BACKEND_URL = os.getenv('RESERVATION_BACKEND_URL', 'http://reservation-service:5003')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hotels')
def hotels():
    try:
        response = requests.get(f'{HOTEL_BACKEND_URL}/hotels')
        hotels = response.json()
    except Exception as e:
        hotels = []
        print(f"Error fetching hotels: {e}")

    for hotel in hotels:
        try:
            room_response = requests.get(f'{ROOM_BACKEND_URL}/rooms/hotel/{hotel["id"]}')
            if room_response.status_code == 200:
                hotel['rooms'] = room_response.json()
            else:
                hotel['rooms'] = []
        except Exception as e:
            hotel['rooms'] = []
            print(f"Error fetching rooms for hotel {hotel['id']}: {e}")

    return render_template('hotels.html', hotels=hotels)

@app.route('/hotels/add', methods=['GET', 'POST'])
def add_hotel():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        facilities = request.form.getlist('facilities')

        try:
            response = requests.post(
                f'{HOTEL_BACKEND_URL}/hotels',
                json={
                    'name': name,
                    'location': location,
                    'facilities': facilities
                }
            )
            if response.status_code == 201:
                return redirect('/hotels')
            else:
                return jsonify(response.json()), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template('add_hotel.html')

@app.route('/rooms/add', methods=['GET', 'POST'])
def add_room():
    hotel_id = request.args.get('hotel_id')
    if request.method == 'POST':
        hotel_id = request.form.get('hotel_id')
        type = request.form.get('type')
        price = request.form.get('price')
        availability = True

        try:
            response = requests.post(
                f'{ROOM_BACKEND_URL}/rooms',
                json={
                    'hotel_id': hotel_id,
                    'type': type,
                    'price': price,
                    'availability': availability
                }
            )
            if response.status_code == 201:
                return redirect('/hotels')
            else:
                return jsonify(response.json()), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template('add_room.html', hotel_id=hotel_id)

@app.route('/rooms')
def rooms():
    try:
        response = requests.get(f'{ROOM_BACKEND_URL}/rooms')
        rooms = response.json()
    except Exception as e:
        rooms = []
        print(f"Error fetching rooms: {e}")

    return render_template('rooms.html', rooms=rooms)

@app.route('/reservations')
def reservations():
    try:
        response = requests.get(f'{RESERVATION_BACKEND_URL}/reservations')
        reservations = response.json()
    except Exception as e:
        reservations = []
        print(f"Error fetching reservations: {e}")

    return render_template('reservations.html', reservations=reservations)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
