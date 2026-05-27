import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# DeepSeek Setup tumhari API key ke sath
client = OpenAI(
    api_key="sk-98f32cf8a0804fb28ddc35cec96d9254", 
    base_url="https://api.deepseek.com"
)

# Humara Auto Parts ka stock
inventory = """
- Honda Civic 2018 Brake Pads: Rs. 4500 (Available)
- Suzuki Alto Filter: Rs. 800 (Available)
- Toyota Corolla 2020 Side Mirror: Rs. 3200 (Out of stock)
"""

def ask_deepseek_salesman(customer_chat):
    customer_chat = str(customer_chat).strip()
    if not customer_chat:
        customer_chat = "Hello"

    # Multi-language ke liye strict rules set kiye hain yahan
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
        temperature=0.4
    )
    return response.choices[0].message.content

# Render par deployment check karne ke liye health route
@app.route('/', methods=['GET'])
def home():
    return "AI Bot is Running Successfully on Render!", 200

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    # Content type safety lagayi hai taaki Render par crash na ho
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    customer_message = data.get("query") or data.get("message") or ""
    
    ai_reply = ask_deepseek_salesman(customer_message)
    return jsonify({"replies": [{"message": ai_reply}]})

if __name__ == '__main__':
    # Render khud port allocate karega, is se 'Port in use' ya 'Crash' nahi hoga
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
