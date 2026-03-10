import telebot
from telebot import types
import sqlite3
import os

# ────────────────────────────────────────
#          Daredevil Group Manager Bot
#         Dev: @I0_I6   |   ძᥲᖇᥱძᥱ᥎Ꭵᥣ
# ────────────────────────────────────────

TOKEN = os.environ.get("5715894811:AAEdH_xnLRq1zoNMvZITgQSpJWn8pPjkb4k")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set!")

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("daredevil.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS owners (chat_id INTEGER, user_id INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS managers (chat_id INTEGER, user_id INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS admins (chat_id INTEGER, user_id INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS replies (chat_id INTEGER, trigger TEXT, response TEXT)")
conn.commit()

pending_replies = {}

def get_owner(chat_id):
    c.execute("SELECT user_id FROM owners WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    return row[0] if row else None

def set_owner(chat_id, user_id):
    c.execute("DELETE FROM owners WHERE chat_id=?", (chat_id,))
    c.execute("INSERT INTO owners VALUES (?, ?)", (chat_id, user_id))
    conn.commit()

def is_manager(chat_id, user_id):
    c.execute("SELECT 1 FROM managers WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    return c.fetchone() is not None

def is_admin(chat_id, user_id):
    c.execute("SELECT 1 FROM admins WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    return c.fetchone() is not None

def add_manager(chat_id, user_id):
    c.execute("INSERT INTO managers VALUES (?, ?)", (chat_id, user_id))
    conn.commit()

def add_admin(chat_id, user_id):
    c.execute("INSERT INTO admins VALUES (?, ?)", (chat_id, user_id))
    conn.commit()

def remove_admin(chat_id, user_id):
    c.execute("DELETE FROM admins WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    conn.commit()

def remove_manager(chat_id, user_id):
    c.execute("DELETE FROM managers WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    conn.commit()

def add_reply(chat_id, trigger, response):
    c.execute("INSERT INTO replies VALUES (?, ?, ?)", (chat_id, trigger, response))
    conn.commit()

def get_replies(chat_id):
    c.execute("SELECT trigger, response FROM replies WHERE chat_id=?", (chat_id,))
    return c.fetchall()

def delete_reply(chat_id, trigger):
    c.execute("DELETE FROM replies WHERE chat_id=? AND trigger=?", (chat_id, trigger))
    conn.commit()

@bot.message_handler(commands=["start"])
def register_owner(message):
    if message.chat.type in ["group", "supergroup"]:
        set_owner(message.chat.id, message.from_user.id)
        bot.reply_to(message, "✅ تم تسجيلك كمالك الجروب.\nالمطور: @I0_I6")

@bot.message_handler(func=lambda m: m.text and m.reply_to_message)
def handle_commands(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_id = message.reply_to_message.from_user.id
    owner = get_owner(chat_id)

    if user_id == owner:
        role = "owner"
    elif is_manager(chat_id, user_id):
        role = "manager"
    elif is_admin(chat_id, user_id):
        role = "admin"
    else:
        role = "member"

    txt = message.text.strip()

    if txt == "رفع مدير" and role == "owner":
        add_manager(chat_id, target_id)
        bot.reply_to(message, "✅ تم رفعه مدير.")
    elif txt == "تنزيل مدير" and role == "owner":
        remove_manager(chat_id, target_id)
        bot.reply_to(message, "✅ تم تنزيله من الإدارة.")
    elif txt == "رفع ادمن" and role in ["owner", "manager"]:
        add_admin(chat_id, target_id)
        bot.reply_to(message, "✅ تم رفعه أدمن.")
    elif txt == "تنزيل ادمن" and role in ["owner", "manager"]:
        remove_admin(chat_id, target_id)
        bot.reply_to(message, "✅ تم تنزيله من الأدمن.")
    elif txt == "حظر" and role in ["owner", "manager", "admin"]:
        bot.ban_chat_member(chat_id, target_id)
        bot.reply_to(message, "🚫 تم حظره.")
    elif txt == "فك الحظر" and role in ["owner", "manager", "admin"]:
        bot.unban_chat_member(chat_id, target_id)
        bot.reply_to(message, "✅ تم فك الحظر.")
    elif txt == "تقييد" and role in ["owner", "manager", "admin"]:
        perms = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(chat_id, target_id, permissions=perms)
        bot.reply_to(message, "🚷 تم تقييده.")
    elif txt == "فك التقييد" and role in ["owner", "manager", "admin"]:
        perms = types.ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                       can_send_other_messages=True, can_add_web_page_previews=True)
        bot.restrict_chat_member(chat_id, target_id, permissions=perms)
        bot.reply_to(message, "✅ تم فك التقييد.")
    elif txt == "مسح" and role in ["owner", "manager", "admin"]:
        bot.delete_message(chat_id, message.reply_to_message.message_id)
        bot.delete_message(chat_id, message.message_id)
    elif txt == "تثبيت" and role in ["owner", "manager", "admin"]:
        bot.pin_chat_message(chat_id, message.reply_to_message.message_id)
        bot.reply_to(message, "📌 تم تثبيت الرسالة.")

    elif txt == "كشف":
        target_user = message.reply_to_message.from_user

        if target_user.id == owner:
            bot_role = "مالك"
        elif is_manager(chat_id, target_user.id):
            bot_role = "مدير"
        elif is_admin(chat_id, target_user.id):
            bot_role = "أدمن"
        else:
            bot_role = "عضو عادي"

        chat_member = bot.get_chat_member(chat_id, target_user.id)
        group_role = chat_member.status
        if group_role == "creator":
            group_role_ar = "مالك"
        elif group_role == "administrator":
            group_role_ar = "مشرف"
        else:
            group_role_ar = "عضو"
        
        username = f"@{target_user.username}" if target_user.username else "لا يوجد"
        
        caption = (
            f"👤 معلومات العضو:\n\n"
            f"• الاسم ⬅️ {target_user.full_name}\n"
            f"• الآيدي ⬅️ `{target_user.id}`\n"
            f"• اليوزر ⬅️ {username}\n"
            f"• الرتبة (في البوت) ⬅️ {bot_role}\n"
            f"• بالمجموعة ⬅️ {group_role_ar}\n"
        )
        bot.reply_to(message, caption, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "اضافة رد")
def start_add_reply(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    owner = get_owner(chat_id)

    if user_id == owner or is_manager(chat_id, user_id) or is_admin(chat_id, user_id):
        pending_replies[user_id] = {"step": 1, "chat_id": chat_id}
        bot.reply_to(message, "✍️ اكتب الآن الجملة اللي عايزني أرد عليها:")
    else:
        bot.reply_to(message, "❌ مش معاك الصلاحية تضيف ردود")

@bot.message_handler(func=lambda m: m.from_user.id in pending_replies)
def add_reply_steps(message):
    data = pending_replies[message.from_user.id]
    if data["step"] == 1:
        data["trigger"] = message.text
        data["step"] = 2
        bot.reply_to(message, "✅ تمام، اكتب الرد اللي عايزني أقوله:")
    elif data["step"] == 2:
        add_reply(data["chat_id"], data["trigger"], message.text)
        bot.reply_to(message, "🎉 تم إضافة الرد بنجاح.")
        del pending_replies[message.from_user.id]

@bot.message_handler(func=lambda m: m.text and m.text.startswith("مسح رد "))
def delete_reply_cmd(message):
    chat_id = message.chat.id
    trigger = message.text.replace("مسح رد ", "").strip()
    delete_reply(chat_id, trigger)
    bot.reply_to(message, f"🗑️ تم مسح الرد على: {trigger}")

@bot.message_handler(func=lambda m: m.text == "عرض الردود")
def list_replies(message):
    replies = get_replies(message.chat.id)
    if replies:
        msg = "📋 الردود المضافة:\n"
        for t, r in replies:
            msg += f"- {t} ➡ {r}\n"
        bot.reply_to(message, msg)
    else:
        bot.reply_to(message, "❌ مفيش ردود مضافة حاليًا.")

@bot.message_handler(func=lambda m: m.text)
def normal_commands(message):
    txt = message.text.strip()
    if txt == "المطور":
        bot.reply_to(message, "👨‍💻 المطور: @I0_I6")
    elif txt == "رتبتي":
        owner = get_owner(message.chat.id)
        if message.from_user.id == owner:
            bot.reply_to(message, "👑 أنت المالك")
        elif is_manager(message.chat.id, message.from_user.id):
            bot.reply_to(message, "🛠️ أنت مدير")
        elif is_admin(message.chat.id, message.from_user.id):
            bot.reply_to(message, "👮‍♂️ أنت أدمن")
        else:
            bot.reply_to(message, "👤 عضو عادي")
    else:
        if "daredevil" in txt.lower() or "دريدفيل" in txt:
            bot.reply_to(message, "قول يا وحش Daredevil 🔥")
        else:
            replies = get_replies(message.chat.id)
            for t, r in replies:
                if t == txt:
                    bot.reply_to(message, r)
                    break

print("🚀 Daredevil Bot شغال على Railway...")
bot.polling(none_stop=True)
