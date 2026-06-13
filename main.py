import os
import requests
from flask import Flask, request

# إلغاء تحذيرات شهادات الـ SSL غير الموثوقة لتجنب السقوط
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

# إعدادات فيسبوك الخاصة بك
FB_TOKEN = "EAAWmvfe5WngBRqZBc1ZCdHZAr7RMNNzW440AxCCfgWdyQ5UI1Qc0blZCIDmssZABhPTP57pz94KBhmqMmXh61AJXbf8Kpt3KRkypBDUlQXlTixhDKUfZCUZBZCZBZAswmm7s5wfZBfxHL25TKZCGSinQP4egVamVPSmxNDfCQEnZBc5WqbZACEsIbnaHXqC4lcxmsUBmYAZB67bcdBWMolJKvNFA2XAUd0ZBxgZDZD"
VERIFY_TOKEN = "Yacin"

user_states = {}

def send_djezzy_otp(msisdn):
    # استخدام نظام الروابط المباشرة المعدلة بالكامل لمحاكاة التطبيق الرسمي
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/otp"
    payload = f"msisdn={msisdn}"
    
    # الـ Headers الرسمية والدقيقة للتطبيق لتخطي جدار حماية جيزي (توليد بيئة حقيقية)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi 9A Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36',
        'X-Requested-With': 'dz.djezzy.internet',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,ar;q=0.6',
        'Connection': 'keep-alive'
    }
    
    try:
        print(f"[+] Sending Djezzy OTP via Bypass Mode for number: {msisdn}")
        # إرسال الطلب عبر السيرفر مباشرة مع الـ Headers المكثفة والآمنة
        response = requests.post(url, data=payload, headers=headers, timeout=12, verify=False)
        print(f"[+] Djezzy API Response Status Code: {response.status_code}")
        print(f"[+] Server Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            return True
    except Exception as e:
        print(f"[-] Advanced Bypass Mode Connection Error: {e}")
        
    return False

def verify_djezzy_otp(msisdn, otp_code):
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/login"
    payload = f"msisdn={msisdn}&otp={otp_code}&grant_type=password"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi 9A Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36',
        'X-Requested-With': 'dz.djezzy.internet'
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=12, verify=False)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            return "wrong_otp"
    except Exception as e:
        print(f"[-] Verification Request Failed: {e}")
    return False

@app.route('/webhook', methods=['GET'])
def facebook_verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge", "")
    return "Verification Error"

@app.route('/webhook', methods=['POST'])
def facebook_webhook():
    data = request.get_json()
    if data and data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event:
                    sender_id = event["sender"]["id"]
                    user_msg = event["message"].get("text", "").strip()
                    digits = ''.join(filter(str.isdigit, user_msg))
                    
                    if user_msg == "🎁 تسجيل 2 جيجا" or user_msg.lower() in ["hello", "start"]:
                        user_states[sender_id] = {"state": "WAITING_FOR_PHONE"}
                        send_fb_message(sender_id, "مرحباً بك في بوت Axo 🤖\nمن فضلك أرسل رقم جيزي الخاص بك (07XXXXXXXX) لبدء التفعيل الفوري:")
                        
                    elif user_states.get(sender_id, {}).get("state") == "WAITING_FOR_PHONE":
                        if len(digits) == 10 and digits.startswith("07"):
                            msisdn = "213" + digits[1:]
                            send_fb_message(sender_id, f"جاري الاتصال بسيرفرات جيزي لإرسال رمز التحقق إلى الرقم {digits}... ⏳⚠️")
                            
                            if send_djezzy_otp(msisdn):
                                user_states[sender_id] = {"state": "WAITING_FOR_OTP", "msisdn": msisdn, "pure_phone": digits}
                                reply = "✅ تم إرسال الرمز بنجاح!\nالرجاء إدخل رمز التحقق (OTP) المكون من 6 أرقام الذي وصلك في رسالة قصيرة SMS:"
                            else:
                                reply = "❌ فشل الاتصال بسيرفر جيزي.\nيرجى التأكد من أن الرقم مسجل في جيزي أو المحاولة مرة أخرى بعد دقيقة."
                                user_states[sender_id] = None
                        else:
                            reply = "❌ الرقم غير صحيح! يرجى إدخال رقم جيزي صحيح يبدأ بـ 07 ويتكون من 10 أرقام:"
                        send_fb_message(sender_id, reply)
                        
                    elif user_states.get(sender_id, {}).get("state") == "WAITING_FOR_OTP":
                        saved_info = user_states[sender_id]
                        if len(digits) == 6:
                            send_fb_message(sender_id, "🔐 جاري التحقق من الرمز وتفعيل الـ 2 جيجا...")
                            auth_result = verify_djezzy_otp(saved_info["msisdn"], digits)
                            
                            if auth_result == "wrong_otp":
                                reply = "❌ الرمز الذي أدخلته خاطئ! أعد إدخال الرمز الصحيح المكون من 6 أرقام:"
                            elif auth_result and "access_token" in auth_result:
                                reply = f"🎉 مبروك! تم تفعيل هدية الـ (2 جيجا مجاناً) بنجاح على رقمك {saved_info['pure_phone']} عبر بوت Axo 🤖!"
                                user_states[sender_id] = None
                            else:
                                reply = "❌ حدث خطأ أثناء تفعيل العرض، يرجى إعادة إرسال رقمك للمحاولة مجدداً."
                                user_states[sender_id] = None
                        else:
                            reply = "⚠️ يرجى إدخال رمز تحقق صحيح مكون من 6 أرقام:"
                        send_fb_message(sender_id, reply)
                    else:
                        send_fb_message(sender_id, "مرحباً بك في بوت أكسو (Axo) لتفعيل عروض الإنترنت 🤖\n\nاضغط على الزر بالأسفل لبدء الاستفادة الفورية 👇")
                        
    return "ok", 200

def send_fb_message(recipient_id, text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={FB_TOKEN}"
    quick_replies = [{"content_type": "text", "title": "🎁 تسجيل 2 جيجا", "payload": "ACTIVATE"}]
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text, "quick_replies": quick_replies}}
    try: requests.post(url, json=payload)
    except: pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
