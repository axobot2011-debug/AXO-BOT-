import os
import requests
import json
from flask import Flask, request

# إلغاء تحذيرات شهادات الـ SSL غير الموثوقة لتجنب مشاكل الاتصال بسيرفر جيزي
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

# إعدادات فيسبوك الخاصة بك
FB_TOKEN = "EAAWmvfe5WngBRifTZBeE3xaYBayhuic05lnkmZA3SpYVZBDG4SVzodCvGZAcxvKBEEx659iUZC6ZAxXZBslKuH6xooPZAnO3ZAEwpwqgw1uiMYningycVaf4j9hQxYRuP3580cT7hsXG6Di3SBjNwFnaQEpiqyOcGYE35ROJPsIuNVtv2H8oGw01X3aNyEbJaoaQBZB20ah2mg3K5a2pxp1gBd0LtsxAZDZD"
VERIFY_TOKEN = "Yacin"

# الرابط الخاص بجلب قائمة البروكسيات من موقعك
PROXY_API_URL = 'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json'

user_states = {}

def get_proxy():
    """
    تحليل البروكسي ومعالجته بدقة متناهية مطابقة لملف الـ PHP
    """
    try:
        res = requests.get(PROXY_API_URL, timeout=5)
        if res.status_code == 200:
            proxies_list = res.json()
            if proxies_list and len(proxies_list) > 0:
                # نأخذ البروكسي الأول وننظفه من أي مسافات
                proxy_str = proxies_list[0].strip()
                parts = proxy_str.split(':')
                
                if len(parts) == 4:
                    ip, port, user, password = parts
                    proxy_url = f"http://{user}:{password}@{ip}:{port}"
                    return {"http": proxy_url, "https": proxy_url}
                elif len(parts) == 2:
                    ip, port = parts
                    proxy_url = f"http://{ip}:{port}"
                    return {"http": proxy_url, "https": proxy_url}
    except Exception as e:
        print(f"[-] Proxy Fetch Error: {e}")
    return None

def send_djezzy_otp(msisdn):
    """
    دالة إرسال الرمز مع آلية ذكية لتجربة الاتصال بالبروكسي وبدونه لتفادي الحظر
    """
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/otp"
    payload = f"msisdn={msisdn}"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }
    
    # محاولة أولى: باستخدام البروكسي المستخرج
    proxies = get_proxy()
    if proxies:
        print(f"[+] Trying to send OTP with proxy: {proxies}")
        try:
            response = requests.post(url, data=payload, headers=headers, proxies=proxies, timeout=8, verify=False)
            print(f"[+] Proxy Response Status: {response.status_code}")
            if response.status_code in [200, 201]:
                return True
        except Exception as e:
            print(f"[-] Proxy Attempt Failed: {e}")
            
    # محاولة ثانية: بدون بروكسي (اتصال مباشر) في حال فشل البروكسي أو عدم توفره
    print("[+] Trying direct connection without proxy...")
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=8, verify=False)
        print(f"[+] Direct Response Status: {response.status_code}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"[-] Direct Attempt Failed: {e}")
        
    return False

def verify_djezzy_otp(msisdn, otp_code):
    """
    التحقق من الرمز مع آلية مزدوجة أيضاً لضمان الاتصال
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
    # تجربة بالبروكسي
    if proxies:
        try:
            response = requests.post(url, data=payload, headers=headers, proxies=proxies, timeout=8, verify=False)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                return "wrong_otp"
        except:
            pass
            
    # تجربة بدون بروكسي
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=8, verify=False)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            return "wrong_otp"
    except Exception as e:
        print(f"Error verify: {e}")
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
                    
                    digits = ''.join(filter(str.isdigit, user_msg))
                    
                    if user_msg == "🎁 تسجيل 2 جيجا" or user_msg.lower() in ["hello", "start"]:
                        user_states[sender_id] = {"state": "WAITING_FOR_PHONE"}
                        reply = "مرحباً بك في بوت Axo 🤖\nمن فضلك أرسل رقم جيزي الخاص بك (مثال: 07XXXXXXXX) لبدء التفعيل الفوري:"
                        send_fb_message(sender_id, reply)
                        
                    elif user_states.get(sender_id, {}).get("state") == "WAITING_FOR_PHONE":
                        if len(digits) == 10 and digits.startswith("07"):
                            msisdn = "213" + digits[1:]
                            
                            send_fb_message(sender_id, f"جاري الاتصال بسيرفرات جيزي لإرسال رمز التحقق إلى الرقم {digits}... ⏳")
                            
                            if send_djezzy_otp(msisdn):
                                user_states[sender_id] = {"state": "WAITING_FOR_OTP", "msisdn": msisdn, "pure_phone": digits}
                                reply = "✅ تم إرسال الرمز بنجاح!\nالرجاء إدخال رمز التحقق (OTP) المكون من 6 أرقام الذي وصلك الآن في رسالة نصية قصيرة SMS:"
                            else:
                                reply = "⚠️ فشل الاتصال بسيرفر جيزي. يرجى التأكد من أن الرقم مسجل في جيزي أو المحاولة مرة أخرى بعد دقيقة."
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
                                reply = "❌ فشل التفعيل بسبب خطأ في اتصال جيزي، يرجى إعادة إرسال رقمك للمحاولة من جديد."
                                user_states[sender_id] = None
                        else:
                            reply = "⚠️ يرجى إدخال رمز تحقق صحيح مكون من 6 أرقام:"
                        send_fb_message(sender_id, reply)
                        
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
