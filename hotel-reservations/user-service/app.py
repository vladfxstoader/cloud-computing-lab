from flask import Flask, request, jsonify
from bcrypt import gensalt, hashpw

app = Flask(__name__)

users = []

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    hashed_pass = hashpw(data['password'].encode('utf-8'), gensalt())
    user = {
        'id': len(users) + 1,
        'name': data['name'],
        'email': data['email'],
        'password': hashed_pass.decode('utf-8')
    }
    users.append(user)
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"]}), 201

@app.route('/users', methods=['GET'])
def get_users():
    public_users = [{"id": user["id"], "name": user["name"], "email": user["email"]} for user in users]
    return jsonify(public_users), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
