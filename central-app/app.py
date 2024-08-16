from flask import Flask, render_template, jsonify
import requests
from fake_data import generate_fake_data

app = Flask(__name__)

# List of node URLs
nodes = [
    # "http://127.0.0.1:5173/session",
    "http://first-node:5000/session",
    "http://second-node:5000/session",
    # "http://third-node:5000",
    # "http://fourth-node:5000",
    # "http://fifth-node:5000"
]

@app.route('/')
def index():
    return render_template('index.html')  # Assume a basic button in HTML


@app.route('/trigger_nodes', methods=['POST'])
def trigger_nodes():
    dat = generate_fake_data()
    responses = []

    for node in nodes:
        try:
            response = requests.post(node, json=dat)  # Use 'dat' instead of 'data'
            if response.status_code == 200:
                try:
                    responses.append(response.json())
                except requests.exceptions.JSONDecodeError:
                    responses.append({
                        'node': node,
                        'status': 'error',
                        'message': 'Invalid JSON in response'
                    })
            else:
                responses.append({
                    'node': node,
                    'status': 'error',
                    'message': f"Failed with status code {response.status_code}"
                })
        except requests.exceptions.RequestException as e:
            responses.append({
                'node': node,
                'status': 'error',
                'message': str(e)
            })

    return jsonify(responses)



if __name__ == '__main__':
    app.run(port=8000)