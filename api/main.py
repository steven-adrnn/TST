from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    users = [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Jane Smith"},
    ]
    return jsonify(users)

@app.route('/api/tools', methods=['GET'])
def get_tools():
    tools = [
        {"id": 1, "name": "Cangkul"},
        {"id": 2, "name": "Pupuk"},
        {"id": 3, "name": "Sprayer"},
    ]
    return jsonify(tools)

if __name__ == '__main__':
    app.run()