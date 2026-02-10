import telebot
import pymongo
from bson.objectid 
import ObjectId
import os
import time
from telebot import types
from keep_alive import keep_alive

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('DB_CHANNEL_ID') 
MONGO_URL = os.environ.get('MONGO_URL')

# 👉 ADMIN ID
ADMIN_ID = 8032684065

# 👉 FORCE SUBSCRIBE
FORCE_SUB_USERNAME = "@anmol_new" 
FORCE_SUB_URL = "https://t.me/anmol_new"

# 👉 BUTTON LINK
YOUR_PERSONAL_LINK = "https://t.me/anmol_new"

# --- DATABASE CONNECT ---
try:
    client = pymongo.MongoClient(MONGO_URL)
    db = client["MovieBotDB_Fresh"] 
    collection = db["movies"]
    users_collection = db["users"] 
    print("✅ Database Connected!")
except Exception as e:
    print(f"❌ Database Error: {e}")

bot = telebot.TeleBot(BOT_TOKEN)

# --- SAVE USER ---
def save_user(user_id):
    try:
        if not users_collection.find_one({"user_id": user_id}):
            users_collection.insert_one({"user_id": user_id})
            print(f"🆕 New User: {user_id}")
    except:
        pass

# --- CHECK MEMBERSHIP ---
def check_membership(user_id):
    try:
        member = bot.get_chat_member(FORCE_SUB_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except:
        return True 

# --- 1. MOVIE SAVING ---
@bot.channel_post_handler(content_types=['video', 'document']) 
def handle_channel_post(message):
    if str(message.chat.id) != str(CHANNEL_ID):
        return
    try:
        file_id = None
        caption = "Unknown"
        
        if message.video:
            file_id = message.video.file_id
            caption = message.caption or message.video.file_name or "Unknown"
        elif message.document:
            file_id = message.document.file_id
            caption = message.caption or message.document.file_name or "Unknown"
            
        if file_id and not collection.find_one({"file_id": file_id}):
            collection.insert_one({"name": caption, "file_id": file_id})
            print(f"✅ Saved: {caption[:15]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

# --- 2. BROADCAST ---
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        return 

    msg_text = message.text.replace('/broadcast', '').strip()
    if not msg_text:
        bot.reply_to(message, "❌ Message missing!")
        return

    bot.reply_to(message, "🚀 Broadcast Started...")
    users = users_collection.find({})
    sent = 0
    
    for user in users:
        try:
            bot.send_message(user['user_id'], msg_text)
            sent += 1
            time.sleep(0.1) 
        except:
            pass
            
    bot.reply_to(message, f"✅ Sent to {sent} users.")

# --- 3. MOVIE SEARCH ---
@bot.message_handler(func=lambda m: True)
def search_movie(message):
    user_id = message.from_user.id
    save_user(user_id)

    if not check_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("🔔 Join Updates Channel", url=FORCE_SUB_URL)
        markup.add(btn1)
        bot.reply_to(message, "⚠️ **Pehle Channel Join karein!** 👇", parse_mode='HTML', reply_markup=markup)
        return
    
    query = message.text.strip()
    result = collection.find_one({"name": {"$regex": query, "$options": "i"}})

    if result:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("⚡ Fast Download / Watch Online ⚡", url=YOUR_PERSONAL_LINK)
        markup.add(btn)

        bot.send_video(
            message.chat.id, 
            result['file_id'], 
            caption=result['name'], 
            parse_mode='HTML', 
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "❌ Movie nahi mili.")

# --- 4. RECENT MOVIES COMMAND ---
@bot.message_handler(commands=['recent'])
def recent_movies(message):
    try:
        # Last 10 movies nikalo (Nayi se Purani)
        recent_docs = collection.find().sort('_id', -1).limit(10)
        
        markup = types.InlineKeyboardMarkup()
        count = 0
        for doc in recent_docs:
            # Button banao: Movie ka Naam -> Click par ID milegi
            btn = types.InlineKeyboardButton(doc['name'], callback_data=f"mov:{doc['_id']}")
            markup.add(btn)
            count += 1
        
        if count == 0:
            bot.reply_to(message, "❌ Abhi tak koi movie nahi dali hai.")
        else:
            bot.reply_to(message, "🎬 **Latest 10 Uploaded Movies:**\nDownload karne ke liye click karein 👇", reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "❌ Error aa gaya.")

# --- 5. BUTTON CLICK HANDLER (Jab user list par click karega) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('mov:'))
def callback_send_movie(call):
    try:
        # Movie ki ID nikalo
        movie_id = call.data.split(':')[1]
        doc = collection.find_one({'_id': ObjectId(movie_id)})
        
        if doc:
            # Wahi button wala link lagayenge
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("⚡ Fast Download / Watch Online ⚡", url=YOUR_PERSONAL_LINK)
            markup.add(btn)
            
            bot.send_video(
                call.message.chat.id,
                doc['file_id'],
                caption=doc['name'],
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(call.id, "❌ Ye movie shayad delete ho gayi hai.")
    except Exception as e:
        print(f"Error: {e}")

# --- SERVER START (FIXED) ---
keep_alive()
print("🤖 Bot Ready! System Online.")

# Yahan humne 'infinity' hata diya hai, ab ye pakka chalega
bot.polling(none_stop=True)
