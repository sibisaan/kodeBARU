import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# URL Endpoint
url_login = 'https://mtacc.mobilelegends.com/v2.1/inapp/login-new'  # Endpoint login yang benar
url_change_email_page = 'https://mtacc.mobilelegends.com/v2.1/inapp/changebindemail'
url_send_verification_code = 'https://api.mobilelegends.com/r'
url_confirm_change_email = 'https://accountmtapi.mobilelegends.com/'

# States untuk Conversational Bot
LOGIN, EMAIL_OLD, CODE_VERIFICATION_OLD, EMAIL_NEW, CODE_VERIFICATION_NEW, VERIFICATION_CODE = range(6)

# Fungsi untuk login dan mendapatkan token otentikasi
def login(email, password):
    data = {
        'email': email,
        'password': password,
        'action': 'login',
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    }

    response = requests.post(url_login, json=data, headers=headers)
    
    # Menyimpan seluruh respons dari API untuk keperluan verifikasi lebih lanjut
    if response.status_code == 200:
        response_data = response.json()
        if 'token' in response_data:
            return response_data  # Mengembalikan seluruh data respons, bukan hanya token
    return None

# Fungsi untuk mengirim kode verifikasi email lama
def send_verification_code(email):
    data = {
        'email': email,
        'action': 'send_verification_code',  # Tentukan aksi yang sesuai
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    }

    response = requests.post(url_send_verification_code, json=data, headers=headers)
    if response.status_code == 200:
        return True
    return False

# Fungsi untuk mengonfirmasi perubahan email dengan kode verifikasi
def confirm_change_email(old_email, new_email, verification_code):
    data = {
        'old_email': old_email,
        'new_email': new_email,
        'verification_code': verification_code
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    }

    response = requests.post(url_confirm_change_email, json=data, headers=headers)
    if response.status_code == 200:
        return True
    return False

# Fungsi untuk mengubah email di endpoint yang sesuai
def change_bind_email(token, old_email, new_email):
    data = {
        'old_email': old_email,
        'new_email': new_email,
        'token': token  # Kirimkan token untuk otentikasi
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    }

    response = requests.post(url_change_email_page, json=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        if 'status' in response_data and response_data['status'] == 'success':
            return True
        elif 'message' in response_data:
            # Jika ada pesan error yang diberikan server
            return response_data['message']
    return 'Gagal melakukan perubahan email.'

# Fungsi start untuk mengawali percakapan
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Halo! Untuk mengubah email Mobile Legends Anda, pertama-tama, silakan login dengan memasukkan email dan password Anda."
    )
    return LOGIN

# Fungsi untuk menerima login (email dan password)
def login_user(update: Update, context: CallbackContext):
    email_password = update.message.text.split()  # Format "email password"
    
    if len(email_password) != 2:
        update.message.reply_text("Format tidak benar. Silakan kirimkan email dan password Anda.")
        return LOGIN
    
    email, password = email_password
    login_response = login(email, password)  # Menyimpan respons API login
    
    if login_response:
        context.user_data['login_response'] = login_response  # Menyimpan respons API login
        token = login_response.get('token')  # Mendapatkan token dari respons
        context.user_data['token'] = token  # Simpan token untuk proses berikutnya
        update.message.reply_text(f"Login berhasil! Anda telah berhasil login sebagai {email}. Sekarang, silakan kirimkan email lama Anda.")
        return EMAIL_OLD
    else:
        update.message.reply_text("Login gagal. Periksa kembali email dan password Anda.")
        return LOGIN

# Fungsi menerima email lama
def receive_old_email(update: Update, context: CallbackContext):
    old_email = update.message.text
    context.user_data['old_email'] = old_email
    
    # Mengirim kode verifikasi ke email lama
    if send_verification_code(old_email):
        update.message.reply_text(f"Kode verifikasi telah dikirim ke {old_email}. Sekarang, silakan kirimkan email baru Anda.")
        return EMAIL_NEW
    else:
        update.message.reply_text("Gagal mengirimkan kode verifikasi. Coba lagi nanti.")
        return ConversationHandler.END

# Fungsi menerima email baru
def receive_new_email(update: Update, context: CallbackContext):
    new_email = update.message.text
    context.user_data['new_email'] = new_email
    update.message.reply_text(f"Email baru Anda adalah: {new_email}. Sekarang, silakan masukkan kode verifikasi yang Anda terima.")
    return CODE_VERIFICATION_NEW

# Fungsi menerima kode verifikasi email baru
def receive_verification_code_new(update: Update, context: CallbackContext):
    verification_code = update.message.text
    old_email = context.user_data['old_email']
    new_email = context.user_data['new_email']
    
    # Mengonfirmasi perubahan email
    if confirm_change_email(old_email, new_email, verification_code):
        update.message.reply_text(f"Email berhasil diubah dari {old_email} ke {new_email}.")
    else:
        update.message.reply_text("Gagal mengubah email. Periksa kembali kode verifikasi yang dimasukkan.")
    
    return ConversationHandler.END

# Fungsi cancel percakapan
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Proses perubahan email dibatalkan.")
    return ConversationHandler.END

# Menjalankan bot
def main():
    # Ganti '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw' dengan token bot Telegram yang didapatkan dari BotFather
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    
    dispatcher = updater.dispatcher
    
    # ConversationHandler untuk mengatur alur percakapan
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOGIN: [MessageHandler(Filters.text & ~Filters.command, login_user)],
            EMAIL_OLD: [MessageHandler(Filters.text & ~Filters.command, receive_old_email)],
            EMAIL_NEW: [MessageHandler(Filters.text & ~Filters.command, receive_new_email)],
            CODE_VERIFICATION_NEW: [MessageHandler(Filters.text & ~Filters.command, receive_verification_code_new)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dispatcher.add_handler(conv_handler)
    
    # Menjalankan bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
