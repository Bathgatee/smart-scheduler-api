import os
import uuid
import csv
from flask import Flask, request, jsonify, send_file
from flask_mail import Mail, Message
from datetime import datetime
import stripe

app = Flask(__name__)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Flask-Mail config
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('EMAIL_USER'),
    MAIL_PASSWORD=os.getenv('EMAIL_PASS')
)
mail = Mail(app)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=[{
            'price': os.getenv('STRIPE_PRICE_ID'),
            'quantity': 1,
        }],
        success_url='https://mfgscheduler.com/thank-you',
        cancel_url='https://mfgscheduler.com/',
    )
    return jsonify({'url': session.url})

@app.route('/webhook', methods=['POST'])
def webhook_received():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session['customer_details']['email']
        license_key = str(uuid.uuid4())

        with open('license_keys.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if csvfile.tell() == 0:
                writer.writerow(['email', 'license_key', 'timestamp'])
            writer.writerow([customer_email, license_key, datetime.utcnow().isoformat()])

        send_license_email(customer_email, license_key)

    return '', 200

@app.route('/verify-key', methods=['POST'])
def verify_key():
    data = request.get_json()
    input_key = data.get('license_key')
    if not input_key:
        return jsonify({'valid': False, 'message': 'No license key provided'}), 400

    try:
        with open('license_keys.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['license_key'] == input_key:
                    return jsonify({'valid': True})
    except FileNotFoundError:
        return jsonify({'valid': False, 'message': 'License database not found'}), 500

    return jsonify({'valid': False, 'message': 'Invalid license key'})

@app.route('/download')
def download():
    return send_file('executable/SmartSchedulerInstaller.exe', as_attachment=True)

def send_license_email(recipient, license_key):
    try:
        msg = Message(
            subject="Your Smart Scheduler License Key",
            sender=app.config['MAIL_USERNAME'],
            recipients=[recipient],
            body=f"Thank you for your purchase!\n\nHere is your license key:\n{license_key}\n\nVisit https://mfgscheduler.com/thank-you to activate and download."
        )
        mail.send(msg)
    except Exception as e:
        print(f"Email send failed: {e}")

if __name__ == '__main__':
    app.run(port=4242)
