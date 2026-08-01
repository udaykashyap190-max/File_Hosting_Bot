from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.auth import register_user, is_admin, get_status

# ==========================================
# MAIN KEYBOARD
# ==========================================
def user_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📤 Upload File", callback_data="upload_file")],
        [InlineKeyboardButton("📁 My Files", callback_data="my_files")],
        [InlineKeyboardButton("⌨️ Input", callback_data="input_panel")],
        [InlineKeyboardButton("📦 Modules", callback_data="modules_panel")],
      
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================================
# ADMIN KEYBOARD
# ==========================================
def admin_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📤 Upload File", callback_data="upload_file")],
        [InlineKeyboardButton("📁 My Files", callback_data="my_files")],
        [InlineKeyboardButton("⌨️ Input", callback_data="input_panel")],
        [InlineKeyboardButton("📦 Modules", callback_data="modules_panel")],
        [InlineKeyboardButton("🌐 Proxy Manager", callback_data="proxy_panel")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================================
# START COMMAND
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        message = update.message

        if user is None or message is None:
            return

        # Register user
        try:
            register_user(user)
        except Exception as e:
            print(f"⚠️ Error registering user: {e}")

        # Check if admin
        if is_admin(user.id):
            await message.reply_text(
                text="👑 Welcome, Admin!\n\nYou have full access to all bot features.",
                reply_markup=admin_main_keyboard()
            )
            return

        # Get user status
        status = get_status(user.id)

        # Approved user
        if status == "approved":
            await message.reply_text(
                text="✅ Your account is approved!\n\nWelcome! You can now use all available bot features.",
                reply_markup=user_main_keyboard()
            )
            return

        # Blocked user
        if status == "blocked":
            await message.reply_text(
                text="🚫 Your account is blocked.\n\nYou cannot use this bot."
            )
            return

        # Pending user
        await message.reply_text(
            text="⏳ Your access request is pending.\n\nYour account needs to be approved by the administrator before you can use the bot."
        )

    except Exception as e:
        print(f"❌ Error in start handler: {e}")
        try:
            await update.message.reply_text("❌ An error occurred. Please try again.")
        except:
            pass
