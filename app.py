from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import random
import string
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Make sure license_keys.json exists and has the correct structure
if not os.path.exists("license_keys.json"):
    with open("license_keys.json", "w") as f:
        json.dump({"keys": []}, f)

# Generate a random license key
def generate_random_license_key(length=16):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

# API endpoint to generate a new license key
@app.route('/generate-license', methods=['POST'])
def generate_license():
    license_key = generate_random_license_key()

    with open("license_keys.json", "r+") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"keys": []}

        if "keys" not in data:
            data["keys"] = []

        data["keys"].append(license_key)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

    return jsonify({"license_key": license_key})

# Health check endpoint
@app.route('/')
def home():
    return 'Smart Scheduler API is running!'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 4242))
    app.run(host='0.0.0.0', port=port)

