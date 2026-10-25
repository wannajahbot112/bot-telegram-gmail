import sqlite3
import telebot
from telebot import types

# === KONFIGURASI ===
TOKEN = "8355336466:AAGcJWxtzkyQ2YCWO-owgUdF-54ZRi0hGkA"
ADMIN_ID = 8590759890  # Telegram ID kamu

bot = telebot.TeleBot(TOKEN)

# === SETUP DATABASE ===
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            saldo INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            account_data TEXT,
            status TEXT DEFAULT 'ready'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper DB
def get_user_saldo(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT saldo FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO users (user_id, saldo) VALUES (?, 0)", (user_id,))
        conn.commit()
        saldo = 0
    else:
        saldo = res[0]
    conn.close()
    return saldo

# === HANDLER MENU UTAMA ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    get_user_saldo(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📦 Cek Stok Akun', '🛒 Beli Akun')
    markup.row('💳 Isi Saldo', '💰 Cek Saldo')
    
    bot.send_message(
        message.chat.id, 
        "👋 Selamat Datang di Bot Jual Beli Email Game!\nSilakan pilih menu di bawah:", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_menu(message):
    user_id = message.from_user.id
    
    if message.text == '📦 Cek Stok Akun':
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT category, COUNT(*) FROM stocks WHERE status='ready' GROUP BY category")
        stocks = cursor.fetchall()
        conn.close()
        
        msg_text = "📦 **STOK AKUN READY:**\n\n"
        if not stocks:
            msg_text += "Stok saat ini sedang kosong."
        else:
            for cat, count in stocks:
                msg_text += f"• {cat}: {count} Akun\n"
        bot.reply_to(message, msg_text, parse_mode="Markdown")

    elif message.text == '💰 Cek Saldo':
        saldo = get_user_saldo(user_id)
        bot.reply_to(message, f"💰 **Saldo Anda Saat Ini:**\nRp {saldo:,}".replace(",", "."))

    elif message.text == '💳 Isi Saldo':
        bot.reply_to(message, "💳 Untuk Top-Up Saldo, silakan hubungi Admin / Transfer via QRIS (Hubungi Admin).")

    elif message.text == '🛒 Beli Akun':
        bot.reply_to(message, "Fitur Beli: Gunakan command `/beli <kategori> <jumlah>`\nContoh: `/beli GMAIL 1`")

# === COMMAND KHUSUS ADMIN (RESTOCK VIA HP) ===
@bot.message_handler(commands=['restock'])
def restock_account(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        lines = message.text.split('\n')
        header = lines[0].split()
        category = header[1].upper()
        
        accounts = lines[1:]
        if not accounts:
            bot.reply_to(message, "❌ Mana daftar emailnya? Masukkan email di baris baru.")
            return

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        count = 0
        for acc in accounts:
            if acc.strip():
                cursor.execute("INSERT INTO stocks (category, account_data) VALUES (?, ?)", (category, acc.strip()))
                count += 1
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ Berhasil menambah **{count}** stok ke kategori **{category}**!")
    except Exception as e:
        bot.reply_to(message, f"❌ Format salah! Gunakan:\n`/restock KATEGORI`\n`email:pass`\n\nDetail: {e}")

# === COMMAND TAMBAH SALDO BY ADMIN ===
@bot.message_handler(commands=['addsaldo'])
def add_saldo(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, amount = message.text.split()
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET saldo = saldo + ? WHERE user_id = ?", (int(amount), int(target_id)))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Saldo user `{target_id}` berhasil ditambah Rp {int(amount):,}")
    except Exception as e:
        bot.reply_to(message, "Format: `/addsaldo <user_id> <nominal>`")

bot.infinity_polling()