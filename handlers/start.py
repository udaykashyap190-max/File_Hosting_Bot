
# handlers/start.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from core.auth import (
    register_user,
    is_admin,
    get_status
)


# ==========================================
# MAIN KEYBOARD
# ==========================================

def user_main_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "📤 Upload File",
                callback_data="upload_file"
            )
        ],

        [
            InlineKeyboardButton(
                "📁 My Files",
                callback_data="my_files"
            )
        ],

        [
            InlineKeyboardButton(
                "⌨️ Input",
                callback_data="input_panel"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 Modules",
                callback_data="modules_panel"
            )
        ],

        [
            InlineKeyboardButton(
                "🌐 Proxy Manager",
                callback_data="proxy_panel"
            )
        ]

    ])


# ==========================================
# ADMIN KEYBOARD
# ==========================================

def admin_main_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "📤 Upload File",
                callback_data="upload_file"
            )
        ],

        [
            InlineKeyboardButton(
                "📁 My Files",
                callback_data="my_files"
            )
        ],

        [
            InlineKeyboardButton(
                "⌨️ Input",
                callback_data="input_panel"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 Modules",
                callback_data="modules_panel"
            )
        ],

        [
            InlineKeyboardButton(
                "🌐 Proxy Manager",
                callback_data="proxy_panel"
            )
        ],

        [
            InlineKeyboardButton(
                "👑 Admin Panel",
                callback_data="admin_panel"
            )

        ]

    ])


# ==========================================
# START COMMAND
# ==========================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    message = update.message

    if user is None or message is None:
        return


    # ======================================
    # REGISTER USER
    # ======================================

    try:

        register_user(user)

    except Exception as e:

        print(
            f"⚠️ Error registering user: {e}"
        )


    # ======================================
    # ADMIN
    # ======================================

    if is_admin(user.id):

        await message.reply_text(

            "👑 Welcome, Admin!\n\n"
            "You have full access to all bot features.",

            reply_markup=
            admin_main_keyboard()

        )

        return


    # ======================================
    # GET USER STATUS
    # ======================================

    status = get_status(
        user.id
    )


    # ======================================
    # APPROVED USER
    # ======================================

    if status == "approved":

        await message.reply_text(

            "✅ Your account is approved!\n\n"
            "Welcome! You can now use all "
            "available bot features.",

            reply_markup=
            user_main_keyboard()

        )

        return


    # ======================================
    # BLOCKED USER
    # ======================================

    if status == "blocked":

        await message.reply_text(

            "🚫 Your account is blocked.\n\n"
            "You cannot use this bot."

        )

        return


    # ======================================
    # PENDING USER
    # ======================================

    await message.reply_text(

        "⏳ Your access request is pending.\n\n"
        "Your account needs to be approved "
        "by the administrator before you can "
        "use the bot."

    )
