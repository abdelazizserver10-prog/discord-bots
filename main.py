import os
from dotenv import load_dotenv
import subprocess
import sys
import threading
import time

# تحميل متغيرات البيئة
load_dotenv()

# قائمة البوتات والتوكنات الخاصة بها
bots = [
    ('arbitration_legend_bot.py', 'ARBITRATION_LEGEND_TOKEN'),
    ('report_shield_bot.py', 'REPORT_SHIELD_TOKEN'),
    ('game_master_bot.py', 'GAME_MASTER_TOKEN'),
    ('audio_master_bot.py', 'AUDIO_MASTER_TOKEN'),
    ('giveaway_master_bot.py', 'GIVEAWAY_MASTER_TOKEN'),
]

print("🚀 بدء تشغيل البوتات الخمسة...")
print("=" * 60)

processes = []

def run_bot(bot_file, token_env):
    """تشغيل بوت واحد"""
    try:
        print(f"⚙️ جاري تشغيل {bot_file}...")
        
        # التحقق من التوكن
        token = os.getenv(token_env)
        if not token:
            print(f"❌ خطأ: {token_env} ليس موجود في Environment Variables!")
            return
        
        # تشغيل البوت
        process = subprocess.Popen([sys.executable, bot_file])
        processes.append((bot_file, process))
        print(f"✅ {bot_file} تم تشغيله!")
        process.wait()
    except Exception as e:
        print(f"❌ خطأ في {bot_file}: {e}")

# شغّل كل بوت في thread منفصل
for bot_file, token_env in bots:
    thread = threading.Thread(target=run_bot, args=(bot_file, token_env), daemon=True)
    thread.start()
    time.sleep(2)

print("=" * 60)
print("✅ جميع البوتات تم تشغيلها!")
print("البوتات تعمل الآن 24/7 ✨")
print("=" * 60)

# احبس البرنامج من الإغلاق
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("⏹️ إيقاف البوتات...")
    for bot_file, process in processes:
        try:
            process.terminate()
        except:
            pass
