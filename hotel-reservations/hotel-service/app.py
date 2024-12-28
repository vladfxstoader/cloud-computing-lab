from flask import Flask, request, jsonify

app = Flask(__name__)

hotels = []

@app.route('/add_hotel', methods=['POST'])
def add_hotel():
    data = request.get_json()
    hotel = {
        'id': len(hotels) + 1,
        'name': data['name'],
        'location': data['location'],
        'facilities': data.get('facilities', [])
    }
    hotels.append(hotel)
    return jsonify(hotel), 201

@app.route('/hotels', methods=['GET'])
def get_hotels():
    return jsonify(hotels), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
