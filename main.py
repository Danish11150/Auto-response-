import os
import json
import requests
from flask import Flask, request, jsonify

# --------- Proxy cleanup for Render (optional but safe) ----------
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""

# --------- Flask app ----------
app = Flask(__name__)

# --------- DeepSeek API Key (set in Render env vars) ----------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()

if not DEEPSEEK_API_KEY:
    print("WARNING: DEEPSEEK_API_KEY is not set. Set it in Render dashboard.")


# --------- Inventory loader ----------
def load_inventory():
    filename = "inventory.txt"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # Fallback inventory
    return """
    - Honda Civic 2018 Brake Pads: Rs. 4500 (Available)
    - Suzuki Alto Filter: Rs. 800 (Available)
    - Toyota Corolla 2020 Side Mirror: Rs. 3200 (Out of stock)
    """


# --------- DeepSeek salesman logic ----------
def ask_deepseek_salesman(customer_chat: str) -> str:
    customer_chat = (customer_chat or "").strip()
    if not customer_chat:
        customer_chat = "Hello"

    current_inventory = load_inventory()

    system_rules = f"""
    You are an expert AI Salesman for Bhaiya's Auto Parts Shop.

    Language Rules:
    - Detect customer's language and script (e.g., Roman Urdu, Urdu, Hindi, Hinglish, English).
    - Always reply in the SAME language and script as the customer.
    - Keep replies short, polite, and professional.
    - If item is out of stock, suggest a close alternative or ask for car model/year.

    Inventory:
    {current_inventory}
    """

    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    payload = {
        "model": "deepseek-chat",  # try deepseek-v4 or deepseek-v4-flash if needed
        "messages": [
            {"role": "system", "content": system_rules},
            {"role": "user", "content": customer_chat},
        ]
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )

        # Log non-200 responses
        if response.status_code != 200:
            print("DeepSeek HTTP Error:", response.status_code, response.text)
            return "Server busy hai, thori der baad try karein."

        data = response.json()
        # Debug log
        # print("DeepSeek JSON:", data)

        if "choices" not in data or not data["choices"]:
            print("DeepSeek invalid response:", data)
            return "AI response mein issue aa gaya, please dobara message bhejein."

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("DeepSeek exception:", e)
        return "Server error aa gaya, thori der baad dobara try karein."


# --------- Health check ----------
@app.route("/", methods=["GET"])
def home():
    return "AI Bot is Running Successfully with External Inventory File!", 200


# --------- WhatsApp webhook (AutoResponder compatible) ----------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    try:
        # Accept both JSON and form data
        data = request.get_json(silent=True) or request.form.to_dict() or {}

        # Common keys AutoResponder / custom webhooks may use
        customer_message = (
            data.get("query")
            or data.get("message")
            or data.get("text")
            or data.get("body")
            or ""
        )

        print("Incoming message:", customer_message, "| Raw data:", data)

        ai_reply = ask_deepseek_salesman(customer_message)

        # AutoResponder usually expects JSON with "replies"
        return jsonify({
            "replies": [
                {"message": ai_reply}
            ]
        })

    except Exception as e:
        print("Webhook exception:", e)
        return jsonify({"error": str(e)}), 500


# --------- Local dev / Render entry ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
