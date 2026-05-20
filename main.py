import os
import requests
import json
import re
from flask import Flask, request

# إلغاء تحذيرات شهادات الـ SSL غير الموثوقة لتجنب مشاكل الاتصال
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

# إعدادات فيسبوك الخاصة بك
FB_TOKEN = "EAAWmvfe5WngBRifTZBeE3xaYBayhuic05lnkmZA3SpYVZBDG4SVzodCvGZAcxvKBEEx659iUZC6ZAxXZBslKuH6xooPZAnO3ZAEwpwqgw1uiMYningycVaf4j9hQxYRuP3580cT7hsXG6Di3SBjNwFnaQEpiqyOcGYE35ROJPsIuNVtv2H8oGw01X3aNyEbJaoaQBZB20ah2mg3K5a2pxp1gBd0LtsxAZDZD"
VERIFY_TOKEN = "Yacin"

PROXY_API_URL = 'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json'

user_states = {}

def get_backup_proxies():
    """
    دالة احتياطية ذكية لجلب بروكسيات مجانية وتجربتها تلقائياً في حال فشل البروكسي الخاص بك
    """
    proxies_found = []
    try:
        # جلب قائمة بروكسيات عامة وسريعة تدعم الـ HTTPS
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            list_p = res.text.strip().split('\n')
            for p in list_p:
                if p.strip():
                    proxies_found.append(p.strip())
    except:
        pass
    return proxies_found

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
    
    # 1. المحاولة بالبروكسي الخاص بموقعك أولاً
    try:
        res = requests.get(PROXY_API_URL, timeout=4)
        if res.status_code == 200:
            my_proxy = res.json()[0].strip()
            parts = my_proxy.split(':')
            if len(parts) == 4:
                p_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            else:
                p_url = f"http://{parts[0]}:{parts[1]}"
            
            print(f"[+] Trying your site proxy...")
            response = requests.post(url, data=payload, headers=headers, proxies={"http": p_url, "https": p_url}, timeout=6, verify=False)
            if response.status_code in [200, 201]:
                return True
    except:
        print("[-] Your proxy failed. Launching Auto-Proxy Search...")

    # 2. إذا فشل، البوت سيبحث تلقائياً عن أي بروكسي شغال ويعبر جدار حماية جيزي فوراً
    backup_list = get_backup_proxies()
    for proxy in backup_list[:15]: # تجربة أفضل 15 بروكسي متاح
        try:
            p_url = f"http://{proxy}"
            print(f"[+] Trying automated backup proxy: {proxy}")
            response = requests.post(url, data=payload, headers=headers, proxies={"http": p_url, "https": p_url}, timeout=4, verify=False)
            if response.status_code in [200, 201]:
                print(f"[🎉] Found working proxy! OTP Sent.")
                return True
        except:
            continue
            
    return False

def verify_djezzy_otp(msisdn, otp_code):
    url = "https://apim.djezzy.dz/mobile-api/api/v1/auth/login"
    payload = f"msisdn={msisdn}&otp={otp_code}&grant_type=password"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)'
    }
    
    # المحاولة الأولى عبر الاتصال المباشر والبروكسي الآلي
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=6, verify=False)
        if response.status_code == 200:
            return response.json()
    except:
        pass
        
    backup_list = get_backup_proxies()
    for proxy in backup_list[:10]:
        try:
            p_url = f"http://{proxy}"
            response = requests.post(url, data=payload, headers=headers, proxies={"http": p_url, "https": p_url}, timeout=4, verify=False)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                return "wrong_otp"
        except:
            continue
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
                            send_fb_message(sender_id, f"جاري تجاوز حظر الشبكة والاتصال بسيرفر جيزي للرقم {digits}... ⏳ (قد يستغرق الأمر ثوانٍ)")
                            
                            if send_djezzy_otp(msisdn):
                                user_states[sender_id] = {"state": "WAITING_FOR_OTP", "msisdn": msisdn, "pure_phone": digits}
                                reply = "✅ تم إرسال الرمز بنجاح!\nالرجاء إدخال رمز التحقق (OTP) المكون من 6 أرقام الذي وصلك في رسالة قصيرة SMS:"
                            else:
                                reply = "❌ عذراً، جميع البروكسيات مضغوطة حالياً وسيرفر جيزي يرفض الاتصال الخارجي. أعد إرسال رقمك للمحاولة مرة أخرى."
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
                                reply = "❌ انتهت صلاحية الجلسة أو حدث خطأ، يرجى إعادة إرسال رقمك للبدء من جديد."
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
