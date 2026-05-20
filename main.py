import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ضع التوكن الخاص بصفحتك هنا مكان العبارة أدناه
FB_TOKEN = "YOUR_FACEBOOK_PAGE_TOKEN"
VERIFY_TOKEN = "Yacin"

# هذا الرابط مخصص فقط لفيسبوك للتحقق من كلمة السر
@app.route('/webhook', methods=['GET'])
def facebook_verify():
    token_sent = request.args.get("hub.verify_token")
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge", "")
    return "Verification Error"

# هذا الرابط مخصص لاستقبال رسائل المستخدمين والرد عليها
@app.route('/webhook', methods=['POST'])
def facebook_webhook():
    data = request.get_json()
    if data and data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event:
                    sender_id = event["sender"]["id"]
                    user_msg = event["message"].get("text", "").strip()
                    
                    if user_msg == "🎁 تسجيل 2 جيجا":
                        reply = "مرحباً بك في Axo 🤖\nمن فضلك أرسل رقم جيزي الخاص بك لبدء التفعيل:"
                    elif user_msg == "ℹ️ شرح البوت":
                        reply = "البوت يساعدك على تفعيل الهدايا تلقائياً عبر خطوات بسيطة."
                    else:
                        reply = "مرحباً بك في بوت Axo 🤖\nاختر من القائمة بالأسفل للبدء."
                        
                    send_fb_message(sender_id, reply)
    return "ok", 200

def send_fb_message(recipient_id, text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={FB_TOKEN}"
    quick_replies = [
        {"content_type": "text", "title": "🎁 تسجيل 2 جيجا", "payload": "ACTIVATE"},
        {"content_type": "text", "title": "ℹ️ شرح البوت", "payload": "ABOUT"}
    ]
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text, "quick_replies": quick_replies}
    }
    try:
        requests.post(url, json=payload)
    except:
        pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
