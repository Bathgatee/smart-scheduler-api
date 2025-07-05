import os
import json
import stripe
import secrets
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Create license_keys.json if it doesn't exist
if not os.path.exists("license_keys.json"):
    with open("license_keys.json", "w") as f:
        json.dump({"keys": []}, f)

# Function to generate a random license key
def generate_random_license_key(length=16):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(secrets.choice(chars) for _ in range(length))

# Health check route
@app.route('/')
def home():
    return "Smart Scheduler API is running!"

# Manual license generation route
@app.route('/generate-license', methods=['POST'])
def generate_license():
    license_key = generate_random_license_key()

    with open("license_keys.json", "r+") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"keys": []}

        data["keys"].append(license_key)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

    return jsonify({"license_key": license_key})

# Stripe webhook listener
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return "Webhook signature verification failed", 400

    if event["type"] == "checkout.session.completed":
        license_key = generate_random_license_key()

        with open("license_keys.json", "r+") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"keys": []}

            data["keys"].append(license_key)
            f.seek(0)

