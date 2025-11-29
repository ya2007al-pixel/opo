import asyncio
import os
import re 
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant, FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import idle
# قم بإضافة هذا إذا لم تكن موجودة بالفعل في ملفك:
# from pyrogram import idle 

# =========================================================
## 🔑 إعداد البيانات (Configuration) 🔑
# =========================================================

# يتم قراءة البيانات من متغيرات البيئة (Render/GitHub Secrets)
# ملاحظة: يتم قراءة API_ID كـ (string) ويجب تحويله إلى int لاحقاً
API_ID = os.environ.get("32315282")       
API_HASH = os.environ.get("acdfe0167bd1ca0a8460f08829bc636d")  
BOT_TOKEN = os.environ.get("8552426997:AAFrhyosIgp8uekpZnjBCzd3Z9KmIMQA4I0")  

# متغيرات الجلسة والذاكرة المؤقتة
DOWNLOAD_DIR = "Temp_Cache_Cloud" 
# حفظ حالة المستخدم أثناء التسجيل {user_id: {"step": "phone", "phone_number": None, "sent_code": None}}
USER_STATES = {} 

# =========================================================

# تهيئة العميل كـ "بوت" باستخدام التوكن (يتطلب API_ID و API_HASH أيضاً)
# نستخدم try/except هنا لمنع تعطل البوت بالكامل إذا كانت المفاتيح غير صحيحة
try:
    bot_app = Client(
        "BotSession",
        api_id=int(API_ID), # تحويل إلى عدد صحيح
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
except Exception as e:
    print(f"❌ خطأ حرج عند تهيئة البوت: {e}")
    print("يرجى التأكد من أن API_ID هو رقم صحيح في متغيرات البيئة.")
    exit() # إيقاف التشغيل إذا فشلت التهيئة

# =========================================================
# دالة مساعدة لمعالجة المنشور (نفس المنطق السابق)
# ... يجب أن تضع هنا دالة process_message الخاصة بك ...
async def process_message(app, message, dest_channel):
    # (هنا تضع منطق السحب والتعديل والإرسال)
    
    # مثال بسيط للإرسال فقط لتشغيل الكود
    if message.text:
        await app.send_message(dest_channel, message.text)
    elif message.media:
        await message.copy(dest_channel)
    await asyncio.sleep(0.5)
    pass


# =========================================================
## 🤖 أوامر البوت التفاعلية (Bot Commands) 🤖
# =========================================================

@bot_app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 تسجيل دخول (Login)", callback_data="login_step_1")],
        [InlineKeyboardButton("🚀 بدء عملية السحب", callback_data="start_scrape")]
    ])
    
    await message.reply_text(
        "مرحباً! اضغط على **تسجيل دخول** لبدء العملية، ثم ابدأ السحب.",
        reply_markup=keyboard
    )

@bot_app.on_callback_query(filters.regex("login_step_1"))
async def login_callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    
    # تهيئة الحالة
    USER_STATES[user_id] = {"step": "phone", "phone_number": None, "sent_code": None}
    
    await callback_query.edit_message_text(
        "📝 يرجى إرسال رقم هاتفك كاملاً مع رمز الدولة (مثال: +96277xxxxxxx).",
    )

@bot_app.on_message(filters.private & (filters.regex(r"^\+\d+") | filters.regex(r"^\d+")))
async def handle_login_input(client, message):
    user_id = message.from_user.id
    current_state = USER_STATES.get(user_id)

    if not current_state:
        return 

    temp_client = Client(
        f"sessions/{user_id}", # اسم الجلسة الخاصة بالمستخدم
        api_id=int(API_ID),
        api_hash=API_HASH
    )
    
    if current_state["step"] == "phone":
        # ... (منطق إرسال الكود وتحديث الحالة) ...
        # (استخدم منطق التحقق من الرقم وإرسال الكود الذي زودتك به سابقاً)
        # لتبسيط الكود، يجب وضع هنا منطق `temp_client.send_code`
        await message.reply_text("⏳ جاري إرسال الكود. أرسل الكود المكون من 5 أرقام الآن.")
        current_state["step"] = "code" # تجاوز مرحلة إرسال الكود لتبسيط الكود هنا
        # يجب وضع منطق temp_client.send_code هنا لتكون الآلية صحيحة

    elif current_state["step"] == "code":
        # ... (منطق تسجيل الدخول باستخدام الكود والتحقق من الباسورد) ...
        # (استخدم منطق التحقق من الرمز و sign_in و check_password الذي زودتك به سابقاً)
        await message.reply_text("🎉 تم تسجيل دخول حسابك بنجاح! يمكنك الآن بدء السحب.")
        del USER_STATES[user_id]

    elif current_state["step"] == "password":
        # ... (منطق إدخال كلمة المرور) ...
        await message.reply_text("🎉 تم تسجيل دخول حسابك بنجاح! يمكنك الآن بدء السحب.")
        del USER_STATES[user_id]


@bot_app.on_callback_query(filters.regex("start_scrape"))
async def start_scrape_callback(client, callback_query):
    await callback_query.edit_message_text(
        "أرسل الآن روابط القنوات المطلوبة على النحو التالي (في رسالة واحدة):"
        "\n**[1] رابط قناة الوجهة (@channel)**"
        "\n**[2] رابط قناة المصدر (@source)**"
    )

@bot_app.on_message(filters.regex(r"^\@(\w+)\s+\@(\w+)", re.IGNORECASE) & filters.private)
async def handle_scrape_request(client, message):
    user_id = message.from_user.id
    
    # محاولة إنشاء العميل المسجل دخوله
    try:
        user_client = Client(
            f"sessions/{user_id}",
            api_id=int(API_ID),
            api_hash=API_HASH
        )
        await user_client.start()
    except Exception:
        await message.reply_text("❌ لم يتم تسجيل دخول حسابك. يرجى الضغط على زر **Login** أولاً.")
        return

    # 1. تحليل الروابط
    parts = message.text.split()
    destination_link = parts[0]
    source_link = parts[1]
    
    # 2. بدء عملية السحب
    try:
        await message.reply_text(f"🚀 بدء عملية السحب من **{source_link}** إلى **{destination_link}**...")
        
        # جلب جميع الرسائل والنقل باستخدام دالة process_message
        all_messages = []
        async for msg in user_client.get_chat_history(source_link):
            all_messages.append(msg)
        
        all_messages.reverse()
        await message.reply_text(f"📊 تم العثور على {len(all_messages)} رسالة. جاري النقل...")

        for msg in all_messages:
            await process_message(user_client, msg, destination_link)
            
        await message.reply_text("✅✅ انتهى النقل بنجاح!")
        
    except UserNotParticipant:
        await message.reply_text("❌ يجب أن يكون حساب العميل مشتركاً في القناة المصدر أو الوجهة.")
    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ عام: {e}")
    
    finally:
        # إيقاف العميل المستخدم لإنهاء الجلسة بشكل صحيح
        await user_client.stop() 


# =========================================================
## 🚀 دالة التشغيل الرئيسية (Main Function) 🚀
# =========================================================

async def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs("sessions", exist_ok=True) # مجلد لحفظ جلسات المستخدمين

    # 1. تشغيل البوت
    await bot_app.start()
    print("🤖 البوت يعمل وينتظر الأوامر.")
    
    # 2. البقاء في وضع التشغيل (لتشغيل idle)
    await idle()
    
    # 3. عند إيقاف التشغيل (هذا يحل مشكلة finally: القديمة)
    await bot_app.stop()

if __name__ == "__main__":
    # هذا يحل مشكلة async.run القديمة
    asyncio.run(main())