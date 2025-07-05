from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import random
import string
import stripe

load_dotenv()

app = Flask(__name__)
CORS(app)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
license_file = "license_keys.json"
installer_path = "downloads"
installer_filename = "SmartSchedulerInstaller_v1.exe"

def generate_license_key(length=16):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route("/generate-license", methods=["POST"])
def generate_license():
    key = generate_license_key()
    if os.path.exists(license_file):
        with open(license_file, "r") as f:
            keys = json.load(f)
    else:
        keys = []
    keys.append(key)
    with open(license_file, "w") as f:
        json.dump(keys, f)
    return jsonify({"license_key": key})

@app.route("/download", methods=["GET"])
def download_file():
    return send_from_directory(installer_path, installer_filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4242))
    app.run(host="0.0.0.0", port=port)
