from flask import Flask, request, jsonify
app = Flask(__name__)

payments = []

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    payment = {
        'id': len(payments) + 1,
        'reservation_id': data['reservation_id'],
        'amount': data['amount'],
        'status': 'confirmed'
    }
    payments.append(payment)
    return jsonify(payment), 201

@app.route('/payments', methods=['GET'])
def get_payments():
    return jsonify(payments), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)