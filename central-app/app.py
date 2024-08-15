from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# List of node URLs
nodes = [
    "http://first-node:5000",
    "http://second-node:5000",
    "http://third-node:5000",
    "http://fourth-node:5000",
    "http://fifth-node:5000"
]

@app.route('/')
def index():
    return render_template('index.html')  # Assume a basic button in HTML

@app.route('/trigger-nodes', methods=['POST'])
def trigger_nodes():
    responses = []
    for node in nodes:
        response = requests.post(f"{node}/session", json={"user_data": "sample data"})
        responses.append(response.json())
    return jsonify(responses)

if __name__ == '__main__':
    app.run(port=5000)