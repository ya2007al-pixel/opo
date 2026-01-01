import asyncio
import os
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from flask import Flask
from threading import Thread

# ==================== 🌐 نظام البقاء حياً ====================
app = Flask('')
@app.route('/')
def home(): return "Turbo Session-Saver Bot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# ==================== 🔑 إعداداتك 🔑 ====================
API_ID = 33296024
API_HASH = "2ca6c382c66fa301a67997270836e933"
BOT_TOKEN = "8498812432:AAGh7AOmkr7zZs-yS8BoqDI7GeZx4DqGOL4"

# ==================== 🤖 إعداد البوت 🤖 ====================
# البوت الأساسي
bot = TelegramClient('bot_main_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# قاموس لحفظ الكليانت المفتوح حالياً في الذاكرة
active_clients = {}

async def turbo_transfer(u_client, bot_client, message, chat_id):
    """نقل صاروخي بالجودة الأصلية"""
    try:
        if not message or not message.media: return
        if hasattr(message.media, 'webpage'): return

        # تحميل الميديا بأقصى سرعة (Telethon يستخدم tgcrypto تلقائياً للسرعة)
        path = await u_client.download_media(message)
        
        if path:
            # الرفع بنفس الجودة والصيغة
            await bot_client.send_file(
                chat_id, 
                path, 
                caption=message.text or "", 
                supports_streaming=True, # لدعم تشغيل الفيديو أثناء التحميل
                force_document=False    # ليرسله كفيديو مشغل وليس كملف صامت (إلا لو كان ملفاً أصلاً)
            )
            if os.path.exists(path): os.remove(path)
    except Exception as e:
        print(f"⚠️ خطأ في النقل: {e}")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    session_file = f"user_{uid}.session"
    
    # محاولة استعادة الجلسة إذا كانت موجودة
    if os.path.exists(session_file):
        if uid not in active_clients:
            client = TelegramClient(f"user_{uid}", API_ID, API_HASH)
            await client.connect()
            if await client.is_user_authorized():
                active_clients[uid] = {'client': client, 'step': 'ready'}
                await event.respond("✅ تم استعادة جلستك السابقة بنجاح! أرسل رابط القناة الآن.")
                return
            else:
                os.remove(session_file) # الجلسة منتهية
    
    active_clients[uid] = {'step': 'phone'}
    await event.respond("🚀 أهلاً بك! لم يتم العثور على جلسة نشطة.\nأرسل رقمك الآن (مثال: +962XXXXXXXX):")

@bot.on(events.NewMessage)
async def handler(event):
    uid = event.sender_id
    text = event.raw_text.strip()
    
    if uid not in active_clients: return

    # خطوة الرقم
    if active_clients[uid]['step'] == 'phone' and text.startswith('+'):
        client = TelegramClient(f"user_{uid}", API_ID, API_HASH)
        await client.connect()
        try:
            sent_code = await client.send_code_request(text)
            active_clients[uid].update({'client': client, 'phone': text, 'hash': sent_code.phone_code_hash, 'step': 'wait_code'})
            await event.respond("📩 أرسل الكود:")
        except Exception as e: await event.respond(f"❌ {e}")

    # خطوة الكود
    elif active_clients[uid]['step'] == 'wait_code':
        data = active_clients[uid]
        try:
            await data['client'].sign_in(data['phone'], text.replace(" ", ""), phone_code_hash=data['hash'])
            data['step'] = 'ready'
            await event.respond("✅ تم الدخول وحفظ الجلسة! أرسل رابط القناة الآن.")
        except Exception as e: await event.respond(f"❌ {e}")

    # خطوة السحب الصاروخي الشامل
    elif (text.startswith('https://t.me/') or text.startswith('@')) and active_clients[uid]['step'] == 'ready':
        u_client = active_clients[uid]['client']
        await event.respond("🌪️ بدأ سحب كامل محتوى القناة بأقصى سرعة... (سأرسل الفيديوهات تباعاً)")
        
        # limit=None يعني سحب كل المقاطع من بداية القناة لنهايتها
        async for msg in u_client.iter_messages(text, limit=None):
            if msg.media:
                # نستخدم await هنا لضمان عدم انفجار الرام في السيرفر المجاني
                # إذا كنت على PC، يمكن تغييرها لـ asyncio.create_task لسرعة جنونية
                await turbo_transfer(u_client, bot, msg, uid)
                await asyncio.sleep(1) # راحة ثانية واحدة للسيرفر

if __name__ == '__main__':
    keep_alive()
    print("🚀 نسخة 'حفظ الجلسة التوربينية' تعمل الآن...")
    bot.run_until_disconnected()