import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# ════════════════════════════════════════════════════════════════════════
# الإعدادات الأساسية (استبدل القيم بما يناسب صفحتك)
# ════════════════════════════════════════════════════════════════════════
FB_TOKEN = "ضع_هنا_التوكن_الخاص_بصفحتك_PAGE_ACCESS_TOKEN"
VERIFY_TOKEN = "Yacin"  # رمز التحقق للـ Webhook

# مجلد مؤقت لحفظ حالات المستخدمين (بديل للمجلدات في PHP)
DATA_DIR = "bot_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ════════════════════════════════════════════════════════════════════════
# دالات محاكاة والاتصال بـ API جيزي (مترجمة من PHP)
# ════════════════════════════════════════════════════════════════════════

def djezzy_send_otp(phone):
    """إرسال طلب OTP إلى رقم الهاتف"""
    # هنا يتم محاكاة الطلب بناءً على كود الـ PHP المرسل
    print(f"[Djezzy API] Sending OTP to: {phone}")
    # في الكود الفعلي يتم إرسال طلب POST إلى سيرفر جيزي
    # payload = "grant_type=password&username=..."
    return True

def djezzy_verify_otp(phone, otp_code):
    """التحقق من كود الـ OTP والحصول على التوكن"""
    print(f"[Djezzy API] Verifying OTP {otp_code} for {phone}")
    # إذا نجح التحقق، يعود بـ access_token
    if len(otp_code) == 6:
        return {"access_token": "mock_access_token_123", "refresh_token": "mock_refresh_123"}
    return False

def djezzy_claim_mgm(access_token):
    """تفعيل مكافأة الـ 2 جيجا (MGM)"""
    print("[Djezzy API] Claiming MGM Reward...")
    return True

# ════════════════════════════════════════════════════════════════════════
# إدارة جلسات المستخدمين (حفظ خطوة المستخدم الحالية)
# ════════════════════════════════════════════════════════════════════════

def get_user_state(sender_id):
    path = os.path.join(DATA_DIR, f"{sender_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"step": "idle", "phone": None}

def set_user_state(sender_id, state):
    path = os.path.join(DATA_DIR, f"{sender_id}.json")
    with open(path, "w") as f:
        json.dump(state, f)

# ════════════════════════════════════════════════════════════════════════
# دالات التعامل مع فيسبوك (إرسال الرسائل والأزرار)
# ════════════════════════════════════════════════════════════════════════

def send_fb_message(recipient_id, text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={FB_TOKEN}"
    
    # القائمة والأزرار التفاعلية الظاهرة أسفل المحادثة
    quick_replies = [
        {"content_type": "text", "title": "🎁 تسجيل 2 جيجا", "payload": "ACTIVATE"},
        {"content_type": "text", "title": "ℹ️ شرح البوت", "payload": "ABOUT"},
        {"content_type": "text", "title": "👨‍💻 المطور", "payload": "DEVELOPER"}
    ]
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text, "quick_replies": quick_replies}
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

# ════════════════════════════════════════════════════════════════════════
# مسارات السيرفر (Flask Webhook)
# ════════════════════════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def facebook_verify():
    # التحقق من الروابط عند إعداد تطبيق مطوري فيسبوك
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge", "")
    return "خطأ في التحقق من التوكن"

@app.route('/', methods=['POST'])
def facebook_webhook():
    data = request.get_json()
    if not data or data.get("object") != "page":
        return "ok", 200

    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            if "message" in messaging_event:
                sender_id = messaging_event["sender"]["id"]
                message_text = messaging_event["message"].get("text", "").strip()
                
                # جلب حالة المستخدم الحالية
                state = get_user_state(sender_id)
                
                # 1. التعامل مع الأزرار العامة والقائمة رئيسية
                if message_text == "🎁 تسجيل 2 جيجا":
                    state["step"] = "awaiting_phone"
                    set_user_state(sender_id, state)
                    send_fb_message(sender_id, "أهلاً بك في خدمة التفعيل التلقائي لـ Axo 🤖\nمن فضلك أرسل رقم هاتف جيزي الخاص بك (مثال: 07xxxxxxxx):")
                    continue
                    
                elif message_text == "ℹ️ شرح البوت":
                    explanation = "شرح البوت 📚:\n1. اضغط على زر تسجيل 2 جيجا.\n2. أدخل رقم هاتف جيزي الخاص بك.\n3. سيصلك رمز تفعيل OTP على هاتفك، أرسله للبوت.\n4. انتظر التفعيل بنجاح!"
                    send_fb_message(sender_id, explanation)
                    continue

                elif message_text == "👨‍💻 المطور":
                    send_fb_message(sender_id, "تم تطوير هذا البوت لمشروع Axo لخدمات التفعيل التلقائي.")
                    continue

                # 2. منطق تتبع الخطوات لعملية التفعيل (State Machine)
                if state["step"] == "awaiting_phone":
                    # التحقق من أن المدخل رقم هاتف جزائري
                    if message_text.startswith("07") and len(message_text) == 10:
                        state["phone"] = message_text
                        # استدعاء دالة طلب OTP
                        if djezzy_send_otp(message_text):
                            state["step"] = "awaiting_otp"
                            set_user_state(sender_id, state)
                            send_fb_message(sender_id, f"تم إرسال رمز التحقق إلى الرقم {message_text}.\nالرجاء إدخال الرمز المكون من 6 أرقام هنا:")
                        else:
                            send_fb_message(sender_id, "فشل إرسال الرمز، يرجى المحاولة لاحقاً.")
                    else:
                        send_fb_message(sender_id, "رقم الهاتف غير صحيح. تأكد من أنه يبدأ بـ 07 ويتكون من 10 أرقام.")
                
                elif state["step"] == "awaiting_otp":
                    # استقبال الرمز والتحقق منه
                    otp = message_text
                    phone = state["phone"]
                    
                    tokens = djezzy_verify_otp(phone, otp)
                    if tokens:
                        send_fb_message(sender_id, "تم التحقق بنجاح! جاري طلب تفعيل الهدية... ⏳")
                        # تفعيل العرض باستخدام التوكن الناتجة
                        if djezzy_claim_mgm(tokens["access_token"]):
                            send_fb_message(sender_id, f"مبروك! 🎉 تم تفعيل عرض الـ 2 جيجا بنجاح للرقم {phone}.")
                        else:
                            send_fb_message(sender_id, "حدث خطأ أثناء تفعيل المكافأة.")
                        
                        # إعادة تعيين الحالة إلى البداية بعد الانتهاء
                        state["step"] = "idle"
                        state["phone"] = None
                        set_user_state(sender_id, state)
                    else:
                        send_fb_message(sender_id, "رمز التحقق خاطئ أو منتهي الصلاحية. حاول مجدداً أو أعد إرسال رقمك.")
                
                else:
                    # الرسالة الترحيبية الافتراضية
                    send_fb_message(sender_id, "مرحباً بك في بوت Axo 🤖\nاستخدم القائمة بالأسفل للبدء:")

    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
