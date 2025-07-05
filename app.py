import os
import json
import stripe
import string
import random
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
app = Flask(__name__)
CORS(app)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
LICENSE_FILE = "license_keys.json"
INSTALLER_PATH = os.path.join("downloads", "SmartSchedulerInstaller_v1.exe")

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        return {}
    with open(LICENSE_FILE, "r") as f:
        return json.load(f)

def save_licenses(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Smart Scheduler License",
                    },
                    "unit_amount": 1999,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel",
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route("/generate-license", methods=["POST"])
def generate_license():
    # Normally you'd validate payment here (e.g., via Stripe webhook)
    license_key = generate_key()
    licenses = load_licenses()
    licenses[license_key] = {
        "issued": datetime.now().strftime("%Y-%m-%d"),
        "expires": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
        "downloads_left": 3
    }
    save_licenses(licenses)
    return jsonify({"license_key": license_key})

@app.route("/validate-license", methods=["POST"])
def validate_license():
    data = request.get_json()
    license_key = data.get("license_key")

    licenses = load_licenses()
    if license_key not in licenses:
        return jsonify({"error": "Invalid license key"}), 400

    entry = licenses[license_key]
    if datetime.strptime(entry["expires"], "%Y-%m-%d") < datetime.now():
        return jsonify({"error": "License key expired"}), 403

    if entry["downloads_left"] <= 0:
        return jsonify({"error": "Download limit reached"}), 403

    if not os.path.exists(INSTALLER_PATH):
        return jsonify({"error": "Installer not found"}), 500

    entry["downloads_left"] -= 1
    save_licenses(licenses)

    return send_file(INSTALLER_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(port=4242)
