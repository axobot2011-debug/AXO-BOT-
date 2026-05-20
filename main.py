import os
import requests
import json
from flask import Flask, request

app = Flask(__name__)

# إعدادات فيسبوك الخاصة بك
FB_TOKEN = "EAAWmvfe5WngBRifTZBeE3xaYBayhuic05lnkmZA3SpYVZBDG4SVzodCvGZAcxvKBEEx659iUZC6ZAxXZBslKuH6xooPZAnO3ZAEwpwqgw1uiMYningycVaf4j9hQxYRuP3580cT7hsXG6Di3SBjNwFnaQEpiqyOcGYE35ROJPsIuNVtv2H8oGw01X3aNyEbJaoaQBZB20ah2mg3K5a2pxp1gBd0LtsxAZDZD"
VERIFY_TOKEN = "Yacin"

# إعدادات روابط جيزي والبروكسي المستخرجة من ملفك
PROXY_API_URL = 'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json'

# قاموس لتخزين حالات المستخدمين أثناء المحادثة
user_states = {}

def get_proxy():
    """
    جلب البروكسيات لتخطي حظر سيرفرات جيزي بناءً على الرابط في ملفك
    """
    try:
        res = requests.get(PROXY_API_URL, timeout=5)
        if res.status_code == 200:
            proxies_list = res.json()
            if proxies_list and len(proxies_list) > 0:
                # نأخذ أول بروكسي متاح كمثال أو يمكنك عمل حلقة تكرارية عليه
                proxy_str = proxies_list[0] # صيغة: ip:port:user:pass أو ip:port
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
        print(f"Proxy error: {e}")
    return None

def send_djezzy_otp(msisdn):
    """
    الـ API الحقيقي المستخرج من ملفك لإرسال الرمز (OTP)
    """
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/otp"
    payload = {"msisdn": msisdn}
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'MobileApp/3.0.0',
        'accept-language': 'ar'
    }
    
    proxies = get_proxy()
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=10)
        # إذا أرجع السيرفر 200 أو 201 فإنه تم الإرسال بنجاح
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return False

def verify_djezzy_otp(msisdn, otp_code):
    """
    الـ API الحقيقي للتحقق من الرمز واستخراج التوكنات لتفعيل العروض والدعوات
    """
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/login"
    payload = {
        "msisdn": msisdn,
        "otp": otp_code,
        "grant_type": "password"
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'MobileApp/3.0.0'
    }
    
    proxies = get_proxy()
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            # إرجاع التوكنات بنجاح
            return {
                "access_token": res_data.get("access_token"),
                "refresh_token": res_data.get("refresh_token")
            }
        elif response.status_code == 400:
            return "wrong_otp"
    except Exception as e:
        print(f"Error verifying OTP: {e}")
    return False

def send_mgm_invitation(sender_msisdn, receiver_msisdn, access_token):
    """
    تطبيق نظام الدعوة MGM المستخرج لإرسال الـ 1 جيجا للداعي و 500 ميجا للمدعو
    """
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/send-invitation/{sender_msisdn}"
    payload = {"msisdnReciever": receiver_msisdn}
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f"Bearer {access_token}",
        'User-Agent': 'MobileApp/3.0.0',
        'accept-language': 'ar'
    }
    
    proxies = get_proxy()
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"MGM Error: {e}")
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
                    
                    # تحويل الرقم إلى صيغة جيزي الدولية (2137xxxxxxxx) عند الحاجة
                    digits = ''.join(filter(str.isdigit, user_msg))
                    
                    # 1. طلب التفعيل الأولي لبوت Axo
                    if user_msg == "🎁 تسجيل 2 جيجا" or user_msg.lower() == "hello" or user_msg.lower() == "start":
                        user_states[sender_id] = {"state": "WAITING_FOR_PHONE"}
                        reply = "مرحباً بك في بوت Axo 🤖\nمن فضلك أرسل رقم جيزي الخاص بك (مثال: 07XXXXXXXX) لبدء التفعيل الفوري والمجاني:"
                        send_fb_message(sender_id, reply)
                        
                    # 2. استقبال رقم الهاتف والاتصال بـ API جيزي لإرسال الرمز
                    elif user_states.get(sender_id, {}).get("state") == "WAITING_FOR_PHONE":
                        if len(digits) == 10 and digits.startswith("07"):
                            msisdn = "213" + digits[1:]
                            send_fb_message(sender_id, f"جاري الاتصال بسيرفرات جيزي لإرسال رمز التحقق إلى الرقم 0{digits[3:]}... ⏳")
                            
                            if send_djezzy_otp(msisdn):
                                user_states[sender_id] = {"state": "WAITING_FOR_OTP", "msisdn": msisdn, "pure_phone": digits}
                                reply = "✅ تم إرسال الرمز بنجاح!\nالرجاء إدخال رمز التحقق (OTP) المكون من 6 أرقام الذي وصلك الآن في رسالة نصية قصيرة SMS:"
                            else:
                                reply = "⚠️ سيرفر جيزي غير متاح حالياً أو هناك مشكلة في البروكسي. يرجى المحاولة لاحقاً."
                                user_states[sender_id] = None
                        else:
                            reply = "❌ الرقم غير صحيح! يرجى إدخال رقم جيزي صحيح يبدأ بـ 07 ويتكون من 10 أرقام:"
                        send_fb_message(sender_id, reply)
                        
                    # 3. استقبال الرمز وتأكيد التسجيل وتفعيل الهدية عبر توكن جيزي
                    elif user_states.get(sender_id, {}).get("state") == "WAITING_FOR_OTP":
                        saved_info = user_states[sender_id]
                        if len(digits) == 6:
                            send_fb_message(sender_id, "🔐 جاري التحقق من الرمز وتأكيد الهوية عبر جيزي...")
                            
                            auth_result = verify_djezzy_otp(saved_info["msisdn"], digits)
                            
                            if auth_result == "wrong_otp":
                                reply = "❌ الرمز الذي أدخلته خاطئ! أعد إدخال الرمز الصحيح المكون من 6 أرقام:"
                            elif auth_result and "access_token" in auth_result:
                                # هنا نقوم بإرسال دعوة الـ MGM تلقائياً لنفسه أو لرقم نظامي لتوليد الإنترنت المجاني (1GB / 500MB) كما في ملفك
                                send_mgm_invitation(saved_info["msisdn"], "213770000000", auth_result["access_token"])
                                
                                reply = f"🎉 مبروك! تم التحقق بنجاح وتفعيل العرض (2 جيجا هدية) على رقمك {saved_info['pure_phone']} لبوت Axo!\nشكراً لاستخدامك خدماتنا 🤖"
                                user_states[sender_id] = None
                            else:
                                reply = "❌ فشل التفعيل بسبب خطأ في اتصال جيزي، يرجى إعادة إرسال رقمك للمحاولة من جديد."
                                user_states[sender_id] = None
                        else:
                            reply = "⚠️ يرجى إدخال رمز صحيح مكون من 6 أرقام:"
                        send_fb_message(sender_id, reply)
                        
                    # 4. الرسالة الترحيبية الافتراضية
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
