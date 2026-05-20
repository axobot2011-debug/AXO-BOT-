import os
import requests
import json
from flask import Flask, request

app = Flask(__name__)

# إعدادات فيسبوك الخاصة بك
FB_TOKEN = "EAAWmvfe5WngBRifTZBeE3xaYBayhuic05lnkmZA3SpYVZBDG4SVzodCvGZAcxvKBEEx659iUZC6ZAxXZBslKuH6xooPZAnO3ZAEwpwqgw1uiMYningycVaf4j9hQxYRuP3580cT7hsXG6Di3SBjNwFnaQEpiqyOcGYE35ROJPsIuNVtv2H8oGw01X3aNyEbJaoaQBZB20ah2mg3K5a2pxp1gBd0LtsxAZDZD"
VERIFY_TOKEN = "Yacin"

# الرابط الخاص بجلب قائمة البروكسيات من موقعك
PROXY_API_URL = 'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json'

# قاموس لتخزين حالات المحادثة للمستخدمين
user_states = {}

def get_proxy():
    """
    جلب أول بروكسي جزائري شغال من الرابط الخاص بك وتجهيزه للبايثون
    """
    try:
        res = requests.get(PROXY_API_URL, timeout=5)
        if res.status_code == 200:
            proxies_list = res.json()
            if proxies_list and len(proxies_list) > 0:
                proxy_str = proxies_list[0]  # صيغة: ip:port:user:pass أو ip:port
                parts = proxy_str.split(':')
                if len(parts) == 4:
                    ip, port, user, password = parts
                    return {
                        "http": f"http://{user}:{password}@{ip}:{port}",
                        "https": f"http://{user}:{password}@{ip}:{port}"
                    }
                elif len(parts) == 2:
                    ip, port = parts
                    return {
                        "http": f"http://{ip}:{port}",
                        "https": f"http://{ip}:{port}"
                    }
    except Exception as e:
        print(f"Proxy config error: {e}")
    return None

def send_djezzy_otp(msisdn):
    """
    الدالة الرسمية والمعدلة للاتصال بسيرفر جيزي وإرسال الرمز (OTP)
    """
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/otp"
    
    # إرسال الداتا بتنسيق x-www-form-urlencoded كما هو محدد بملف الـ PHP تماماً
    payload = f"msisdn={msisdn}"
    
    # الـ Headers الرسمية المأخوذة من تطبيق جيزي لتخطي الحظر
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }
    
    proxies = get_proxy()
    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxies, timeout=10, verify=False)
        # طباعة كود الحالة للمساعدة في تتبع الأخطاء في Render Logs
        print(f"Djezzy Response Code: {response.status_code}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error calling Djezzy API: {e}")
        return False

def verify_djezzy_otp(msisdn, otp_code):
    """
    التحقق من رمز الـ OTP المدخل واستخراج التوكنات
    """
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/login"
    payload = f"msisdn={msisdn}&otp={otp_code}&grant_type=password"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }
    proxies = get_proxy()
    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxies, timeout=10, verify=False)
        if response.status_code == 200:
            res_data = response.json()
            return {
                "access_token": res_data.get("access_token"),
                "refresh_token": res_data.get("refresh_token")
            }
        elif response.status_code == 400:
            return "wrong_otp"
    except Exception as e:
        print(f"Error verifying OTP: {e}")
    return False

@app.route('/webhook', methods=['GET'])
def facebook_verify():
    token_sent = request.args.get("hub.verify_token")
    if token_sent == VERIFY_TOKEN:
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
                    
                    # استخراج الأرقام فقط من الرسالة
                    digits = ''.join(filter(str.isdigit, user_msg))
                    
                    # 1. عند ضغط زر طلب التسجيل
                    if user_msg == "🎁 تسجيل 2 جيجا" or user_msg.lower() in ["hello", "start"]:
                        user_states[sender_id] = {"state": "WAITING_FOR_PHONE"}
                        reply = "مرحباً بك في بوت Axo 🤖\nمن فضلك أرسل رقم جيزي الخاص بك (مثال: 07XXXXXXXX) لبدء التفعيل الفوري:"
                        send_fb_message(sender_id, reply)
                        
                    # 2. استقبال الرقم وإرسال طلب الـ OTP
                    elif user_states.get(sender_id, {}).get("state") == "WAITING_FOR_PHONE":
                        if len(digits) == 10 and digits.startswith("07"):
                            # تصحيح تحويل الرقم للصيغة الدولية الصافية لجيزي (2137xxxxxxxx)
                            msisdn = "213" + digits[1:]
                            
                            send_fb_message(sender_id, f"جاري الاتصال بسيرفرات جيزي لإرسال رمز التحقق إلى الرقم 0{msisdn[3:]}... ⏳")
                            
                            if send_djezzy_otp(msisdn):
                                user_states[sender_id] = {"state": "WAITING_FOR_OTP", "msisdn": msisdn, "pure_phone": digits}
                                reply = "✅ تم إرسال الرمز بنجاح!\nالرجاء إدخال رمز التحقق (OTP) المكون من 6 أرقام الذي وصلك الآن في رسالة نصية قصيرة SMS:"
                            else:
                                reply = "⚠️ سيرفر جيزي غير متاح حالياً أو هناك مشكلة في البروكسي الخارجي. يرجى المحاولة لاحقاً."
                                user_states[sender_id] = None
                        else:
                            reply = "❌ الرقم غير صحيح! يرجى إدخال رقم جيزي صحيح يبدأ بـ 07 ويتكون من 10 أرقام:"
                        send_fb_message(sender_id, reply)
                        
                    # 3. استقبال رمز التحقق ومعالجته
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
                                reply = "❌ فشل التفعيل بسبب خطأ في اتصال جيزي، يرجى إعادة إرسال رقمك للمحاولة من جديد."
                                user_states[sender_id] = None
                        else:
                            reply = "⚠️ يرجى إدخال رمز تحقق صحيح مكون من 6 أرقام:"
                        send_fb_message(sender_id, reply)
                        
                    # 4. الرد الافتراضي
                    else:
                        reply = "مرحباً بك في بوت أكسو (Axo) لتفعيل عروض الإنترنت 🤖\n\nاضغط على الزر بالأسفل لبدء الاستفادة الفورية 👇"
                        send_fb_message(sender_id, reply)
                        
    return "ok", 200

def send_fb_message(recipient_id, text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={FB_TOKEN}"
    quick_replies = [
        {"content_type": "text", "title": "🎁 تسجيل 2 جيجا", "payload": "ACTIVATE"}
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
