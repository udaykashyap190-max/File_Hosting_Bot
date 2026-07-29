
# handlers/upload.py

import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from core.auth import has_access
from database import add_file


# ==========================================
# UPLOAD FOLDER
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==========================================
# UPLOAD FILE HANDLER
# ==========================================

async def upload_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return


    # ======================================
    # CHECK ACCESS
    # ======================================

    if not has_access(user.id):

        await message.reply_text(
            "🚫 You don't have permission "
            "to use the file runner.\n\n"
            "Please wait for the administrator "
            "to approve your account."
        )

        return


    # ======================================
    # CHECK DOCUMENT
    # ======================================

    document = message.document

    if document is None:

        await message.reply_text(
            "❌ Please send a Python `.py` file."
        )

        return


    # ======================================
    # GET FILE NAME
    # ======================================

    filename = document.file_name

    if not filename:

        await message.reply_text(
            "❌ Could not determine the file name."
        )

        return


    # ======================================
    # ONLY PYTHON FILES
    # ======================================

    if not filename.lower().endswith(".py"):

        await message.reply_text(
            "❌ Only Python `.py` files "
            "are supported."
        )

        return


    # ======================================
    # SAFE FILE NAME
    # ======================================

    filename = os.path.basename(
        filename
    )


    # ======================================
    # USER-SPECIFIC FOLDER
    # ======================================

    user_folder = os.path.join(
        UPLOAD_FOLDER,
        str(user.id)
    )

    os.makedirs(
        user_folder,
        exist_ok=True
    )


    # ======================================
    # FINAL FILE PATH
    # ======================================

    filepath = os.path.join(
        user_folder,
        filename
    )


    # ======================================
    # DOWNLOAD FILE
    # ======================================

    try:

        telegram_file = await document.get_file()

        await telegram_file.download_to_drive(
            custom_path=filepath
        )

    except Exception as e:

        print(
            f"❌ Upload error: {e}"
        )

        await message.reply_text(
            "❌ Failed to upload file.\n\n"
            f"Error: {e}"
        )

        return


    # ======================================
    # SAVE FILE IN DATABASE
    # ======================================

    try:

        file_id = add_file(
            user_id=user.id,
            filename=filename,
            file_path=filepath,
            log_path=""
        )

        print(
            f"✅ DATABASE SAVED | "
            f"user_id={user.id} | "
            f"filename={filename} | "
            f"file_id={file_id}"
        )

    except Exception as e:

        print(
            f"❌ Database error: {e}"
        )

        await message.reply_text(
            "⚠️ File was downloaded, "
            "but could not be saved in the database.\n\n"
            f"Error: {e}"
        )

        return


    # ======================================
    # SAVE ACTIVE FILE
    # ======================================

    context.user_data[
        "active_file"
    ] = filename

    context.user_data[
        "active_file_id"
    ] = file_id


    # ======================================
    # SUCCESS BUTTONS
    # ======================================

    keyboard = InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "📁 My Files",
                callback_data="my_files"
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
                "⬅️ Back",
                callback_data="back_home"
            )

        ]

    ])


    # ======================================
    # SUCCESS MESSAGE
    # ======================================

    await message.reply_text(

        "✅ File uploaded successfully!\n\n"

        f"📄 File: `{filename}`\n"

        f"🆔 File ID: `{file_id}`\n\n"

        "You can now manage your file "
        "from 📁 My Files.",

        parse_mode="Markdown",

        reply_markup=keyboard

    )

