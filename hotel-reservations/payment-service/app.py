import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurația bazei de date
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@payment-db:5432/payment_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='confirmed')

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "Payment service is running!"

@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    if not data or 'reservation_id' not in data or 'amount' not in data:
        return jsonify({"error": "Invalid input"}), 400

    new_payment = Payment(
        reservation_id=data['reservation_id'],
        amount=data['amount']
    )
    db.session.add(new_payment)
    db.session.commit()
    return jsonify({
        "id": new_payment.id,
        "reservation_id": new_payment.reservation_id,
        "amount": new_payment.amount,
        "status": new_payment.status
    }), 201

@app.route('/payments', methods=['GET'])
def get_payments():
    payments = Payment.query.all()
    payment_list = [
        {
            "id": payment.id,
            "reservation_id": payment.reservation_id,
            "amount": payment.amount,
            "status": payment.status
        }
        for payment in payments
    ]
    return jsonify(payment_list), 200

@app.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    return jsonify({
        "id": payment.id,
        "reservation_id": payment.reservation_id,
        "amount": payment.amount,
        "status": payment.status
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
