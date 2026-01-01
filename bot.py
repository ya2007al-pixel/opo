import asyncio
import os
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError, PhoneCodeInvalidError
from flask import Flask
from threading import Thread

# ==================== 🌐 نظام البقاء حياً (Render) ====================
app = Flask('')
@app.route('/')
def home(): return "I am alive"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# ==================== 🔑 إعداداتك 🔑 ====================
API_ID = 33296024
API_HASH = "2ca6c382c66fa301a67997270836e933"
BOT_TOKEN = "8498812432:AAGh7AOmkr7zZs-yS8BoqDI7GeZx4DqGOL4"

# ==================== 🤖 إعداد البوت 🤖 ====================
# ملاحظة: استخدمنا 'bot_instance' ليكون منفصلاً تماماً
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# قاموس لحفظ الكليانت "نفسه" لضمان عدم انتهاء الكود
active_clients = {}

async def hyper_transfer(u_client, bot_client, message, chat_id):
    """محرك النقل الصاروخي"""
    try:
        if not message or not message.media: return
        # منع سحب الروابط والمعاينات
        if hasattr(message.media, 'webpage'): return

        path = await u_client.download_media(message)
        if path:
            await bot_client.send_file(chat_id, path, caption=message.text or "", supports_streaming=True)
            if os.path.exists(path): os.remove(path)
    except Exception as e:
        print(f"⚠️ خطأ في النقل: {e}")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    # تنظيف أي محاولة قديمة
    if uid in active_clients: active_clients.pop(uid)
    await event.respond("👋 أهلاً بك!\nأرسل رقمك الآن مع مفتاح الدولة (مثال: +962XXXXXXXX):")

@bot.on(events.NewMessage)
async def handler(event):
    uid = event.sender_id
    text = event.raw_text.strip()
    
    # 1. مرحلة إرسال الرقم
    if text.startswith('+') and uid not in active_clients:
        # إنشاء الكليانت وحفظه "حياً" في القاموس
        client = TelegramClient(f"user_{uid}", API_ID, API_HASH)
        await client.connect()
        try:
            sent_code = await client.send_code_request(text)
            # حفظ كل المعلومات في كائن واحد لا يتغير
            active_clients[uid] = {
                'client': client,
                'phone': text,
                'hash': sent_code.phone_code_hash,
                'step': 'wait_code'
            }
            await event.respond("📩 أرسل الكود الذي وصلك الآن (تأكد من كتابته بسرعة):")
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    # 2. مرحلة إدخال الكود (هنا تم الإصلاح الحاسم)
    elif uid in active_clients and active_clients[uid]['step'] == 'wait_code':
        data = active_clients[uid]
        u_client = data['client'] # استخدام نفس الكليانت الذي طلب الكود
        
        try:
            clean_code = text.replace(" ", "")
            await u_client.sign_in(data['phone'], clean_code, phone_code_hash=data['hash'])
            data['step'] = 'ready'
            await event.respond("✅ تم الدخول بنجاح! أرسل رابط القناة الآن.")
        except SessionPasswordNeededError:
            data['step'] = 'wait_2fa'
            await event.respond("🔐 الحساب محمي بكلمة سر، أرسلها الآن:")
        except (PhoneCodeExpiredError, PhoneCodeInvalidError):
            await event.respond("❌ الكود خاطئ أو منتهي. أرسل /start وابدأ من جديد فوراً.")
            active_clients.pop(uid)
        except Exception as e:
            await event.respond(f"❌ حدث خطأ: {e}")

    # 3. مرحلة كلمة السر (2FA)
    elif uid in active_clients and active_clients[uid]['step'] == 'wait_2fa':
        try:
            await active_clients[uid]['client'].sign_in(password=text)
            active_clients[uid]['step'] = 'ready'
            await event.respond("✅ تم التحقق! أرسل رابط القناة.")
        except Exception as e:
            await event.respond(f"❌ كلمة سر خاطئة.")

    # 4. مرحلة السحب
    elif (text.startswith('https://t.me/') or text.startswith('@')) and uid in active_clients:
        if active_clients[uid]['step'] == 'ready':
            u_client = active_clients[uid]['client']
            await event.respond("🌪️ بدأ السحب التوربيني... راقب الخاص.")
            
            async for msg in u_client.iter_messages(text, limit=100):
                if msg.media:
                    asyncio.create_task(hyper_transfer(u_client, bot, msg, uid))
                elif msg.text:
                    await bot.send_message(uid, msg.text)
                await asyncio.sleep(0.1)

if __name__ == '__main__':
    keep_alive()
    print("🚀 المحرك النووي يعمل.. تم إصلاح مشكلة الكود.")
    bot.run_until_disconnected()