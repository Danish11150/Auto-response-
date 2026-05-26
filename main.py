import os
from flask import Flask, request, jsonify
from openai import OpenAI
import httpx

app = Flask(__name__)

# Proxy bug ko bypass karne ke liye saaf HTTP client banaya
http_client = httpx.Client(proxies={})

# DeepSeek Setup naye client ke sath taaki 'proxies' wala error khatam ho jaye
client = OpenAI(
    api_key="sk-98f32cf8a0804fb28ddc35cec96d9254", 
    base_url="https://api.deepseek.com",
    http_client=http_client
)

inventory = """
- Honda Civic 2018 Brake Pads: Rs. 4500 (Available)
- Suzuki Alto Filter: Rs. 800 (Available)
- Toyota Corolla 2020 Side Mirror: Rs. 3200 (Out of stock)
"""

def ask_deepseek_salesman(customer_chat):
    customer_chat = str(customer_chat).strip()
    if not customer_chat:
        customer_chat = "Hello"

    system_rules = f"""
    You are an expert AI Salesman for Bhaiya's Auto Parts Shop.
    
    CRITICAL RULE for Language:
    1. Detect the language and script of the customer's message (e.g., Hinglish, English, Urdu, Hindi, Roman Urdu/Hindi).
    2. ALWAYS reply in the SAME language and script that the customer used.
    3. Keep the tone very polite, professional, and short.
    
    Our Inventory:
    {inventory}
    """
    
    response = client.chat.completions.create(
        model="deepseek-v4-flash", 
        messages=[
            {"role": "system", "content": system_rules},
            {"role": "user", "content": customer_chat}
        ],
        temperature=0.5
    )
    return response.choices[0].message.content

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    data = request.get_json()
    customer_message = data.get("query") or data.get("message") or ""
    
    ai_reply = ask_deepseek_salesman(customer_message)
    return jsonify({"replies": [{"message": ai_reply}]})

if __name__ == '__main__':
    # Render ke automatic port setting ka fix
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
