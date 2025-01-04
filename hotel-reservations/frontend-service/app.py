from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
import requests
import os
import jwt
import re
from functools import wraps
from prometheus_client import Counter, generate_latest

app = Flask(__name__)
app.config['SECRET_KEY'] = 'MySecretKey1@'

http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])

@app.before_request
def before_request():
    http_requests_total.labels(request.method, request.endpoint).inc()

@app.route('/metrics', methods=['GET'])
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

HOTEL_BACKEND_URL = os.getenv('HOTEL_BACKEND_URL', 'http://hotel-service:5001')
ROOM_BACKEND_URL = os.getenv('ROOM_BACKEND_URL', 'http://room-service:5002')
RESERVATION_BACKEND_URL = os.getenv('RESERVATION_BACKEND_URL', 'http://reservation-service:5003')
USER_BACKEND_URL = os.getenv('USER_BACKEND_URL', 'http://user-service:5000')
PAYMENT_BACKEND_URL = os.getenv('PAYMENT_BACKEND_URL', 'http://payment-service:5004')

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'\d', password):
        return "Password must contain at least one digit."
    return None

def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('login'))
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_token
def index():
    return render_template('index.html')

@app.route('/hotels')
@require_token
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
@require_token
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
@require_token
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
@require_token
def rooms():
    try:
        response = requests.get(f'{ROOM_BACKEND_URL}/rooms')
        rooms = response.json()
    except Exception as e:
        rooms = []
        print(f"Error fetching rooms: {e}")

    return render_template('rooms.html', rooms=rooms)


@app.route('/rooms/reserve', methods=['POST'])
@require_token
def reserve_room():
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'))
    decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    email = decoded.get('email')

    try:
        user_response = requests.get(f'{USER_BACKEND_URL}/users/email/{email}')
        if user_response.status_code != 200:
            return jsonify({"error": "User not found"}), 404
        user_id = user_response.json().get('id')
    except Exception as e:
        return jsonify({"error": f"Error fetching user data: {str(e)}"}), 500

    data = request.form
    room_id = data.get('room_id')
    check_in = data.get('check_in')
    check_out = data.get('check_out')

    try:
        reservation_response = requests.post(
            f'{RESERVATION_BACKEND_URL}/reservations',
            json={
                'user_id': user_id,
                'room_id': room_id,
                'check_in': check_in,
                'check_out': check_out
            }
        )
        if reservation_response.status_code != 201:
            return jsonify({"error": "Failed to create reservation"}), reservation_response.status_code

        room_response = requests.put(
            f'{ROOM_BACKEND_URL}/rooms/{room_id}',
            json={'availability': False}
        )
        if room_response.status_code != 200:
            return jsonify({"error": "Failed to update room availability"}), room_response.status_code

        return redirect('/hotels')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/reservations')
@require_token
def reservations():
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'))
    decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    email = decoded.get('email')

    try:
        user_response = requests.get(f'{USER_BACKEND_URL}/users/email/{email}')
        if user_response.status_code != 200:
            return jsonify({"error": "User not found"}), 404
        user_id = user_response.json().get('id')
    except Exception as e:
        return jsonify({"error": f"Error fetching user data: {str(e)}"}), 500

    try:
        reservations_response = requests.get(f'{RESERVATION_BACKEND_URL}/reservations/user/{user_id}')
        if reservations_response.status_code != 200:
            return jsonify({"error": "Failed to fetch reservations"}), reservations_response.status_code

        reservations = reservations_response.json()

        detailed_reservations = []
        for reservation in reservations:
            reservation_id = reservation['id']
            try:
                details_response = requests.get(f'{RESERVATION_BACKEND_URL}/reservations/details/{reservation_id}')
                if details_response.status_code == 200:
                    details = details_response.json()

                    try:
                        payment_response = requests.get(f'{PAYMENT_BACKEND_URL}/payments/reservation/{reservation_id}')
                        if payment_response.status_code == 200:
                            payment_data = payment_response.json()
                            details['payment'] = payment_data['amount']
                            details['status'] = payment_data['status']
                        else:
                            details['payment'] = "N/A"
                            details['status'] = "Not Paid"
                    except Exception as e:
                        details['payment'] = "Error"
                        details['status'] = "Error fetching payment"

                    detailed_reservations.append(details)
            except Exception as e:
                print(f"Error fetching details for reservation {reservation_id}: {e}")

        return render_template('reservations.html', reservations=detailed_reservations)
    except Exception as e:
        return jsonify({"error": f"Error fetching reservations: {str(e)}"}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            response = requests.post(
                f'{USER_BACKEND_URL}/login',
                json={'email': email, 'password': password}
            )

            if response.status_code == 200:
                user_data = response.json()
                token = jwt.encode({'email': email}, app.config['SECRET_KEY'], algorithm='HS256')

                resp = redirect(url_for('index'))
                resp.set_cookie('token', token)
                return resp
            else:
                return render_template('login.html', error="Invalid email or password")

        except Exception as e:
            return render_template('login.html', error=f"Error: {str(e)}")

    return render_template('login.html', error="")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            response = requests.get(f'{USER_BACKEND_URL}/users/email/{email}')
            if response.status_code == 200:
                return render_template('register.html', error="Error: Email already exists.")
        except Exception as e:
            if response.status_code != 404:
                return render_template('register.html', error=f"Error: {str(e)}")

        password_error = validate_password(password)
        if password_error:
            return render_template('register.html', error=password_error)
        
        try:
            response = requests.post(
                f'{USER_BACKEND_URL}/users',
                json={'name': name, 'email': email, 'password': password}
            )

            if response.status_code == 201:
                return redirect('/login')
            else:
                return render_template('register.html', error="Error: " + response.json().get("error", "Unknown error"))

        except Exception as e:
            return render_template('register.html', error=f"Error: {str(e)}")

    return render_template('register.html')

@app.route('/logout')
def logout():
    resp = redirect(url_for('login'))
    resp.delete_cookie('token')
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
