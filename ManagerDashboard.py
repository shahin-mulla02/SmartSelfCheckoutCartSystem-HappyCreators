from flask import Flask, render_template_string, jsonify
import threading
import webbrowser
import json
import os
import time
app = Flask(__name__)

SCANNED_ITEMS_PATH = "static/scanned_items.json"
PAYMENT_STATUS_PATH = "static/payment_status.json"

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get("username")
    password = request.form.get("password")

    # ✅ Always clear scanned items and payment status when new login happens
    with open("static/scanned_items.json", "w") as f:
        json.dump([], f)

    with open(PAYMENT_STATUS_PATH, "w") as f:
       json.dump({
        "cart": "123",
        "status": "Paid successfully",
        "timestamp": time.time()
    }, f)

    speak_welcome()


@app.route('/')
def manager_dashboard():
    # Load scanned items
    if os.path.exists(SCANNED_ITEMS_PATH):
        with open(SCANNED_ITEMS_PATH) as f:
            scanned_items = json.load(f)
    else:
        scanned_items = []

    # Load payment status
    if os.path.exists(PAYMENT_STATUS_PATH):
        with open(PAYMENT_STATUS_PATH) as f:
            payment_status = json.load(f)
            cart_status = payment_status.get("status", "")
    else:
        cart_status = ""

    total_items = sum(item["quantity"] for item in scanned_items)
    total_price = sum(item["price"] * item["quantity"] for item in scanned_items)

    # DON'T clear files here to allow live update JS to keep reading fresh data

    return render_template_string(html, total_items=total_items, total_price=total_price, cart_status=cart_status)

import time  # ✅ Add this at the top of your file

import time  # make sure this is at the top

@app.route('/manager/live-data')
def live_data():
    if os.path.exists(SCANNED_ITEMS_PATH):
        with open(SCANNED_ITEMS_PATH) as f:
            scanned_items = json.load(f)
    else:
        scanned_items = []

    if os.path.exists(PAYMENT_STATUS_PATH):
        with open(PAYMENT_STATUS_PATH) as f:
            payment_status = json.load(f)
            cart_status = payment_status.get("status", "")
            timestamp = payment_status.get("timestamp", 0)

        # ✅ Only clear if more than 300 seconds (5 min) have passed
        if cart_status and (time.time() - timestamp) > 1000:
            with open(PAYMENT_STATUS_PATH, "w") as f:
                json.dump({"cart_id": "", "status": "", "timestamp": 0}, f)
    else:
        cart_status = ""

    total_items = sum(item["quantity"] for item in scanned_items)
    total_price = sum(item["price"] * item["quantity"] for item in scanned_items)

    return jsonify({
        "total_items": total_items,
        "total_price": total_price,
        "cart_status": cart_status
    })



html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Manager Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-800 text-white font-sans min-h-screen flex flex-col">

  <div class="w-full text-center py-6 bg-gray-900 shadow-md">
    <h1 class="text-4xl font-extrabold">SMART SELF-CHECKOUT</h1>
    <p class="text-lg text-gray-300">MANAGER PANEL</p>
  </div>

  <div class="flex-grow flex items-center justify-center">
    <div class="w-full max-w-7xl px-6">

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
        <div class="bg-white text-black rounded-2xl p-8 shadow-xl text-center">
          <span class="text-3xl block mb-2">🛒</span>
          <p class="text-gray-700 text-lg">Active Carts</p>
          <p class="text-2xl font-bold">12</p>
        </div>
        <div class="bg-white text-black rounded-2xl p-8 shadow-xl text-center">
          <span class="text-3xl block mb-2">💾</span>
          <p class="text-gray-700 text-lg">Items Scanned Today</p>
          <p id="totalItems" class="text-2xl font-bold">{{ total_items }}</p>
        </div>
        <div class="bg-white text-black rounded-2xl p-8 shadow-xl text-center">
          <span class="text-3xl block mb-2">💰</span>
          <p class="text-gray-700 text-lg">Total Revenue</p>
          <p id="totalPrice" class="text-2xl font-bold">₹{{ total_price }}</p>
        </div>
        <div class="bg-white text-black rounded-2xl p-8 shadow-xl text-center">
          <span class="text-3xl block mb-2">⏱️</span>
          <p class="text-gray-700 text-lg">Avg. Checkout Time</p>
          <p class="text-2xl font-bold">1 min 42 sec</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 class="text-2xl font-semibold mb-4 text-center">LIVE ACTIVITY</h2>
          <div class="bg-gray-700 p-6 rounded-xl mb-5">
            <p class="text-white font-semibold text-lg">
              Cart #103 – <span id="liveTotalItems">{{ total_items }}</span> items – ₹<span id="liveTotalPrice">{{ total_price }}</span>
            </p>
            <p id="cartStatus" class="text-green-400 text-sm"> {{ cart_status }}</p>
          </div>
          <div class="bg-gray-700 p-6 rounded-xl">
            <p class="text-white font-semibold text-lg">Cart #104 – Scanning item:</p>
            <p class="text-gray-300 text-sm">Dairy Milk (₹40)</p>
          </div>
        </div>

        <div>
          <h2 class="text-2xl font-semibold mb-4 text-center">ALERTS</h2>
          <div class="bg-white text-black p-6 rounded-xl mb-5 flex items-start gap-3 shadow">
            <span class="text-red-600 text-2xl">⚠️</span>
            <p class="text-lg">Cart #107 inactive for 10 minutes</p>
          </div>
          <div class="bg-white text-black p-6 rounded-xl flex items-start gap-3 shadow">
            <span class="text-red-600 text-2xl">⚠️</span>
            <p class="text-lg">Item mismatch detected in Cart 1112</p>
          </div>
        </div>
      </div>

    </div>
  </div>

  <script>
    function fetchLiveData() {
      fetch('/manager/live-data')
        .then(response => response.json())
        .then(data => {
          document.getElementById('totalItems').textContent = data.total_items;
          document.getElementById('totalPrice').textContent = '₹' + data.total_price;
          document.getElementById('liveTotalItems').textContent = data.total_items;
          document.getElementById('liveTotalPrice').textContent = data.total_price;
          document.getElementById('cartStatus').textContent = '🟢 ' + data.cart_status;
        })
        .catch(err => console.error('Error fetching live data:', err));
    }

    setInterval(fetchLiveData, 5000);  // fetch every 5 seconds
  </script>

</body>
</html>
"""

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=False)
