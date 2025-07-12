from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    print("Received data:", data)
    return jsonify({"status": "success", "message": "Data received", "data": data})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
