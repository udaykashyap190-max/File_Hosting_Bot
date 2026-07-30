# handlers/input.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from core.auth import has_access

from core.process import (
    send_input,
    is_running,
    is_waiting_for_input
)


# ==========================================
# STATE
# ==========================================
WAITING_FOR_INPUT = 1


# ==========================================
# INPUT HANDLER
# ==========================================
async def input_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is not None:
        data = query.data or ""

        if data.startswith("input_file|"):
            filename = data.split("|", 1)[1].strip()
            if filename:
                context.user_data["active_file"] = filename

        elif not context.user_data.get("active_file"):
            context.user_data["active_file"] = ""

        return await input_panel(update, context)

    # For safety, if called with a message (rare), route to receive_input
    if update.message is not None:
        return await receive_input(update, context)

    return await input_panel(update, context)


# ==========================================
# INPUT PANEL
# ==========================================
async def input_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    # If this was called as a message handler (fallback), return the state
    if query is None:
        return WAITING_FOR_INPUT

    await query.answer()

    user = query.from_user
    if user is None:
        return ConversationHandler.END

    # ======================================
    # CHECK ACCESS
    # ======================================
    if not has_access(user.id):
        await query.edit_message_text(
            "🚫 You don't have permission "
            "to use this feature."
        )
        return ConversationHandler.END

    # ======================================
    # CHECK ACTIVE FILE
    # ======================================
    filename = context.user_data.get("active_file")
    running_state = context.user_data.get("active_file_running")

    if running_state is None and filename:
        try:
            running_state = is_running(filename)
        except Exception:
            running_state = False
    elif running_state is None:
        running_state = False

    if not filename:
        await query.edit_message_text(
            "⌨️ Input Manager\n\n"
            "❌ No file selected.\n\n"
            "Please open 📁 My Files and "
            "select a running file first.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📁 My Files",
                        callback_data="my_files"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="back_home"
                    )
                ]
            ])
        )
        return ConversationHandler.END

    # ======================================
    # CHECK RUNNING
    # ======================================
    if not running_state and not is_running(filename):
        await query.edit_message_text(
            "⌨️ Input Manager\n\n"
            f"📄 File: `{filename}`\n\n"
            "❌ This file is not running.\n\n"
            "Start the file first from "
            "📁 My Files.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📁 My Files",
                        callback_data="my_files"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="back_home"
                    )
                ]
            ])
        )
        return ConversationHandler.END

    # ======================================
    # INPUT REQUEST
    # ======================================
    waiting = is_waiting_for_input(filename)

    if waiting:
        status_text = "⏳ The file is waiting for input."
    else:
        status_text = "ℹ️ The file is currently running."

    await query.edit_message_text(
        "⌨️ Input Manager\n\n"
        f"📄 File: `{filename}`\n\n"
        f"{status_text}\n\n"
        "✍️ Send your input as a normal "
        "message in this chat.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📁 My Files",
                    callback_data="my_files"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back_home"
                )
            ]
        ])
    )

    # Save selected file
    context.user_data["input_file"] = filename

    return WAITING_FOR_INPUT


# ==========================================
# RECEIVE INPUT
# ==========================================
async def receive_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    message = update.message

    if user is None or message is None:
        return ConversationHandler.END

    # ======================================
    # CHECK ACCESS
    # ======================================
    if not has_access(user.id):
        await message.reply_text(
            "🚫 You don't have permission "
            "to use this feature."
        )
        return ConversationHandler.END

    # ======================================
    # GET SELECTED FILE
    # ======================================
    filename = context.user_data.get("input_file")

    if not filename:
        await message.reply_text(
            "❌ No file is selected.\n\n"
            "Open the Input Manager again "
            "from the main menu."
        )
        return ConversationHandler.END

    # ======================================
    # CHECK RUNNING
    # ======================================
    if not is_running(filename):
        await message.reply_text(
            f"❌ `{filename}` is no longer running.",
            parse_mode="Markdown"
        )
        context.user_data.pop("input_file", None)
        return ConversationHandler.END

    # ======================================
    # GET INPUT
    # ======================================
    value = message.text

    if value is None:
        await message.reply_text("❌ Please send text input.")
        return WAITING_FOR_INPUT

    # ======================================
    # SEND INPUT TO PROCESS
    # ======================================
    success, result = send_input(
        filename,
        value
    )

    if success:
        await message.reply_text(
            "✅ Input sent successfully!\n\n"
            f"📄 File: `{filename}`\n"
            f"⌨️ Input: `{value}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⌨️ Send Another Input",
                        callback_data="input_panel"
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
                        "⬅️ Back",
                        callback_data="back_home"
                    )
                ]
            ])
        )
    else:
        await message.reply_text(
            result,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📁 My Files",
                        callback_data="my_files"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="back_home"
                    )
                ]
            ])
        )

    # Keep file selected so user can send another input
    return WAITING_FOR_INPUT


# ==========================================
# CANCEL INPUT
# ==========================================
async def cancel_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.pop("input_file", None)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🏠 Main Menu\n\n"
            "Choose an option.",
            reply_markup=InlineKeyboardMarkup([
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
        )

    return ConversationHandler.END


# ==========================================
# CONVERSATION HANDLER (export)
# ==========================================
def get_input_conversation_handler():
    """
    Conversation handler that:
    - Entry: CallbackQuery input_panel / input_file
    - State WAITING_FOR_INPUT: accepts text messages and forwards them to running process
    - Fallbacks: cancel input
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                input_handler,
                pattern=r"^input_(?:panel|file)(?:\|.+)?$"
            )
        ],
        states={
            WAITING_FOR_INPUT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_input
                )
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_input, pattern=r"^back_home$"),
            CallbackQueryHandler(cancel_input, pattern=r"^my_files$"),
            CallbackQueryHandler(cancel_input, pattern=r"^input_panel$")
        ],
        per_user=True,
        per_chat=True,
        allow_reentry=True
    )
