import os
import requests
import json
import re
from flask import Flask, request

# إلغاء تحذيرات شهادات الـ SSL غير الموثوقة
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

# إعدادات فيسبوك الخاصة بك
FB_TOKEN = "EAAWmvfe5WngBRifTZBeE3xaYBayhuic05lnkmZA3SpYVZBDG4SVzodCvGZAcxvKBEEx659iUZC6ZAxXZBslKuH6xooPZAnO3ZAEwpwqgw1uiMYningycVaf4j9hQxYRuP3580cT7hsXG6Di3SBjNwFnaQEpiqyOcGYE35ROJPsIuNVtv2H8oGw01X3aNyEbJaoaQBZB20ah2mg3K5a2pxp1gBd0LtsxAZDZD"
VERIFY_TOKEN = "Yacin"

PROXY_API_URL = 'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json'

user_states = {}

def get_algerian_backup_proxies():
    """
    جلب بروكسيات تدعم شمال إفريقيا والجزائر لضمان موافقة سيرفر جيزي
    """
    proxies_found = []
    try:
        # جلب البروكسيات المتاحة جغرافياً والمفتوحة مجاناً
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=6000&country=DZ,MA,TN,FR,IT&ssl=all&anonymity=all"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            list_p = res.text.strip().split('\n')
            for p in list_p:
                if p.strip():
                    proxies_found.append(p.strip())
    except:
        pass
    return proxies_found

def parse_proxy_string(proxy_str):
    proxy_str = proxy_str.strip()
    parts = proxy_str.split(':')
    if len(parts) == 4:
        # صيغة IP:PORT:USER:PASS
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    elif len(parts) == 2:
        # صيغة IP:PORT
        return f"http://{parts[0]}:{parts[1]}"
    return None

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
    
    # 1. محاولة جلب كل البروكسيات المتاحة من رابط موقعك وتجربتها واحداً تلو الآخر
    try:
        res = requests.get(PROXY_API_URL, timeout=5)
        if res.status_code == 200:
            proxy_list = res.json()
            if isinstance(proxy_list, list):
                print(f"[+] Found {len(proxy_list)} proxies in your site file.")
                for raw_proxy in proxy_list:
                    p_url = parse_proxy_string(raw_proxy)
                    if not p_url: continue
                    try:
                        print(f"[+] Trying site proxy: {raw_proxy}")
                        response = requests.post(url, data=payload, headers=headers, proxies={"http": p_url, "https": p_url}, timeout=5, verify=False)
                        if response.status_code in [200, 201]:
                            return True
                    except:
                        continue
            elif isinstance(proxy_list, str):
                p_url = parse_proxy_string(proxy_list)
                if p_url:
                    response = requests.post(url, data=payload, headers=headers, proxies={"http": p_url, "https": p_url}, timeout=5, verify=False)
                    if response.status_code in [200, 201]:
                        return True
    except Exception as e:
        print(f"[-] Site proxy fetch error: {e}")

    print("[-] All site proxies failed. Launching Geo-Targeted Backup Proxies...")

    # 2. خطة الاحتياط الجغرافي (تجنب الحظر الجغرافي لجيزي)
    backup_list = get_algerian_backup_proxies()
    for proxy in backup_list[:20]:
        try:
            p_url = f"http://{proxy}"
            print(f"[+] Trying localized backup proxy: {proxy}")
            response = requests.post(url, data=payload, headers=headers, proxies={"http": p_url, "https": p_url}, timeout=4, verify=False)
            if response.status_code in [200, 201]:
                print(f"[🎉] Bypass Successful! OTP Sent.")
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
    
    # محاولة التحقق عبر البروكسيات أولاً
    try:
        res = requests.get(PROXY_API_URL, timeout=5)
        if res.status_code == 200:
            proxy_list = res.json()
            proxies_to_try = proxy_list if isinstance(proxy_list, list) else [proxy_list]
            for raw_proxy in proxies_to_try:
                p_url = parse_proxy_string(raw_proxy)
                if not p_url: continue
                try:
                    response = requests.post(url, data=payload, headers=headers, proxies={"http": p_url, "https": p_url}, timeout=5, verify=False)
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 400:
                        return "wrong_otp"
                except:
                    continue
    except:
        pass
        
    # الاحتياط الجغرافي للتحقق
    backup_list = get_algerian_backup_proxies()
    for proxy in backup_list[:15]:
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
                            send_fb_message(sender_id, f"جاري فحص وتحديث البروكسيات لتجاوز حظر الشبكة وإرسال الرمز للرقم {digits}... ⏳")
                            
                            if send_djezzy_otp(msisdn):
                                user_states[sender_id] = {"state": "WAITING_FOR_OTP", "msisdn": msisdn, "pure_phone": digits}
                                reply = "✅ تم إرسال الرمز بنجاح!\nالرجاء إدخل رمز التحقق (OTP) المكون من 6 أرقام الذي وصلك في رسالة قصيرة SMS:"
                            else:
                                reply = "❌ تعذر الاتصال بسيرفر جيزي حالياً لأن البروكسيات المتوفرة محظورة جغرافياً. يرجى إعادة إرسال رقمك بعد دقيقة لإعادة المحاولة ببروكسي جديد."
                                user_states[sender_id] = None
                        else:
                            reply = "❌ الرقم غير صحيح! يرجى إدخال رقم جيزي صحيح يبدأ بـ 07 ويتكون من 10 أرقام:"
                        send_fb_message(sender_id, reply)
                        
                    elif user_states.get(sender_id, {}).get("state") == "WAITING_FOR_OTP":
                        saved_info = user_states[sender_id]
                        if len(digits) == 6:
                            send_fb_message(sender_id, "🔐 جاري التحقق من الرمز عبر النفق الآمن وتفعيل الـ 2 جيجا...")
                            auth_result = verify_djezzy_otp(saved_info["msisdn"], digits)
                            
                            if auth_result == "wrong_otp":
                                reply = "❌ الرمز الذي أدخلته خاطئ! أعد إدخال الرمز الصحيح المكون من 6 أرقام:"
                            elif auth_result and "access_token" in auth_result:
                                reply = f"🎉 مبروك! تم تفعيل هدية الـ (2 جيجا مجاناً) بنجاح على رقمك {saved_info['pure_phone']} عبر بوت Axo 🤖!"
                                user_states[sender_id] = None
                            else:
                                reply = "❌ انتهت صلاحية الجلسة أو حظر السيرفر الطلب، يرجى إعادة إرسال رقمك للبدء من جديد."
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
