from flask import Flask, render_template, request, send_file, jsonify
import webbrowser
import threading
import json
import os
from scanner import speak_welcome
from flask import make_response
from flask import Flask, render_template, request, send_file, jsonify
import smtplib
from email.mime.text import MIMEText
import threading
import webbrowser
from openai import OpenAI
from flask import request, jsonify
import os

app = Flask(__name__)

# Sanitize username for file names
def sanitize_username(username):
    return username.replace("@", "_at_").replace(".", "_dot_")

@app.route('/')
def show_login():
    response = make_response(render_template("customer1_dashboard.html"))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get("username")
    password = request.form.get("password")

    # ✅ Clear scanned items first
    with open("static/scanned_items.json", "w") as f:
        json.dump([], f)

    speak_welcome()

    with open("static/login_flag.json", "w") as f:
        json.dump({"just_logged_in": True}, f)

    with open("static/login_data.json", "w") as f:
        json.dump({"username": username,}, f)

    scanned_items = []
    return render_template("customer2_dashboard.html", username=username, scanned_items=scanned_items)



@app.route('/get-login-flag')
def get_login_flag():
    flag_file = "static/login_flag.json"
    if os.path.exists(flag_file):
        with open(flag_file) as f:
            data = json.load(f)
        # Reset the flag after checking
        with open(flag_file, "w") as f:
            json.dump({"just_logged_in": False}, f)
        return jsonify(data)
    return jsonify({"just_logged_in": False})



@app.route('/get-scanned-items')
def get_scanned_items():
    try:
        with open("static/login_data.json") as f:
            username = json.load(f)["username"]
    except:
        return jsonify([])

    safe_user = sanitize_username(username)
    scanned_file = f"static/scanned_items.json"
    try:
        with open(scanned_file) as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify([])

@app.route('/payment-success', methods=['POST'])
def payment_success():
    with open("static/payment_status.json", "w") as f:
        json.dump({"cart": "103", "status": "Paid Successfully"}, f, indent=4)

    try:
        with open("static/login_data.json") as f:
            username = json.load(f)["username"]
            safe_user = sanitize_username(username)
            with open(f"static/scanned_items.json", "w") as f2:
                json.dump([], f2, indent=4)
    except:
        pass

    return render_template("customer2_dashboard.html", username="Customer", scanned_items=[])

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5001/")
@app.route('/download-receipt')
def download_receipt():
    try:
        with open("static/login_data.json") as f:
            username = json.load(f)["username"]
    except:
        return "No login data found", 400

    scanned_file = "static/scanned_items.json"
    try:
        with open(scanned_file) as f:
            scanned_items = json.load(f)
    except FileNotFoundError:
        scanned_items = []

    total = sum(item['price'] * item['quantity'] for item in scanned_items)
    lines = ["Smart Self-Checkout Receipt\n\n"]
    for item in scanned_items:
        lines.append(f"{item['name']} x{item['quantity']} - ₹{item['price']} each\n")
    lines.append(f"\nTotal: ₹{total}")

    receipt_path = "static/receipt.txt"
    with open(receipt_path, "w", encoding="utf-8") as f:
        f.writelines(lines)  # Write receipt lines

    return send_file(receipt_path, as_attachment=True)



@app.route('/email-receipt', methods=['POST'])
def email_receipt():
    try:
        with open("static/login_data.json") as f:
            receiver_email = json.load(f)["username"]
    except:
        return jsonify({"error": "No login data"}), 400

    receipt_path = "static/receipt.txt"
    if not os.path.exists(receipt_path):
        return jsonify({"error": "Receipt not found"}), 404

    # Read receipt content
    with open(receipt_path, "r", encoding="utf-8") as f:
        receipt_content = f.read()

    # Setup email (sender credentials must be YOUR email + app password)
    sender_email = "shahinmulla851@gmail.com"
    sender_password = "cpjzalkralnkyxjh"  # Use app password here

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    import smtplib

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Your Smart Self-Checkout Receipt"

    # Email body
    msg.attach(MIMEText("Please find your receipt attached.", "plain"))

    # Attach receipt file
    with open(receipt_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename=receipt.txt")
    msg.attach(part)

    # Send email via Gmail SMTP
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Email sent successfully to", receiver_email)
        return jsonify({"status": "Email sent"})
    except Exception as e:
        import traceback
        print("Email sending error:")
        traceback.print_exc()  # This prints full error stack trace in console
        return jsonify({"error": str(e)}), 500

from flask import request

@app.route('/ask-ai', methods=['POST'])
def ask_ai():
    data = request.get_json()
    question = data.get('question', '').lower()

    # Simple rule-based answers (replace with AI integration later)
    if "price" in question:
        answer = "The prices are listed next to each item in your cart."
    elif "payment" in question:
        answer = "You can pay via Credit/Debit Card, UPI, or Cash."
    elif "how" in question:
        answer = "Simply scan items and proceed to payment to checkout."
    
    else:
        answer = "I'm here to help! Please ask about products or payment."
    

    return jsonify({"answer": answer})


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5001/")  # or your desired port

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=False, port=5001)  # match the port here and in URL

