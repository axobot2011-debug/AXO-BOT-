import os
import requests
from flask import Flask, request

# إلغاء تحذيرات شهادات الـ SSL غير الموثوقة
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

# إعدادات فيسبوك الخاصة بك
FB_TOKEN = "EAAWmvfe5WngBRifTZBeE3xaYBayhuic05lnkmZA3SpYVZBDG4SVzodCvGZAcxvKBEEx659iUZC6ZAxXZBslKuH6xooPZAnO3ZAEwpwqgw1uiMYningycVaf4j9hQxYRuP3580cT7hsXG6Di3SBjNwFnaQEpiqyOcGYE35ROJPsIuNVtv2H8oGw01X3aNyEbJaoaQBZB20ah2mg3K5a2pxp1gBd0LtsxAZDZD"
VERIFY_TOKEN = "Yacin"

# 🌟 ضع البروكسي الجزائري الجديد هنا مباشرة بين القوسين 🌟
ALGERIAN_PROXY = "105.235.132.88:8080"

user_states = {}

def send_djezzy_otp(msisdn):
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/otp"
    payload = f"msisdn={msisdn}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }
    
    # تجهيز البروكسي المكتوب في الأعلى
    p_url = f"http://{ALGERIAN_PROXY}"
    proxies = {"http": p_url, "https": p_url}
    
    try:
        print(f"[+] Trying Djezzy OTP using proxy: {ALGERIAN_PROXY}")
        response = requests.post(url, data=payload, headers=headers, proxies=proxies, timeout=12, verify=False)
        print(f"[+] Djezzy Response Code: {response.status_code}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"[-] Proxy Request Failed: {e}")
    return False

def verify_djezzy_otp(msisdn, otp_code):
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/login"
    payload = f"msisdn={msisdn}&otp={otp_code}&grant_type=password"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)'
    }
    p_url = f"http://{ALGERIAN_PROXY}"
    proxies = {"http": p_url, "https": p_url}
    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxies, timeout=12, verify=False)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            return "wrong_otp"
    except Exception as e:
        print(f"[-] Verify Proxy Request Failed: {e}")
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
                                reply = "✅ تم إرسال الرمز بنجاح!\nالرجاء إدخال رمز التحقق (OTP) المكون من 6 أرقام الذي وصلك في رسالة قصيرة SMS:"
                            else:
                                reply = "❌ فشل الاتصال بسيرفر جيزي. يرجى التأكد من أن الرقم مسجل في جيزي أو المحاولة مرة أخرى بعد دقيقة."
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
    app.run(host="0.0.0.0", port=5000)
