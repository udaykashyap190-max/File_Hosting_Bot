# handlers/modules.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import subprocess
import sys
import os


# ==========================================
# CONVERSATION STATE
# ==========================================

WAITING_FOR_MODULE = 1


# ==========================================
# COMPATIBILITY HANDLERS
# ==========================================

async def modules_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query is not None:
        data = query.data or ""

        if "|" in data:
            filename = data.split("|", 1)[1].strip()

            if filename:
                context.user_data["active_file"] = filename

    return await modules_menu(update, context)


async def show_modules(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    return await modules_menu(update, context)


async def add_module(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    return await ask_module(update, context)


async def remove_module(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    return await cancel_module(update, context)


# ==========================================
# MODULE MENU
# ==========================================

async def modules_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:
        await query.answer()

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "📦 Install Module",
                    callback_data="module_install"
                )
            ],

            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back_home"
                )
            ]

        ])

        await query.edit_message_text(

            "📦 Module Manager\n\n"
            "You can install Python modules required "
            "by your uploaded files.\n\n"
            "Example:\n"
            "`requests`\n"
            "`beautifulsoup4`\n"
            "`python-telegram-bot`\n\n"
            "Choose an option below.",

            reply_markup=keyboard,

            parse_mode="Markdown"

        )

    return ConversationHandler.END


# ==========================================
# ASK MODULE NAME
# ==========================================

async def ask_module(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(

        "📦 Install Python Module\n\n"
        "Send me the module/package name you want "
        "to install.\n\n"
        "Example:\n"
        "`requests`\n\n"
        "Or multiple modules separated by spaces:\n"
        "`requests bs4 colorama`",

        reply_markup=InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="modules_menu"
                )
            ]

        ]),

        parse_mode="Markdown"

    )

    return WAITING_FOR_MODULE


# ==========================================
# INSTALL MODULE
# ==========================================

async def install_module(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:

        return ConversationHandler.END


    module_text = (
        update.message.text or ""
    ).strip()


    if not module_text:

        await update.message.reply_text(

            "❌ Please enter a valid module name."

        )

        return WAITING_FOR_MODULE


    # ======================================
    # BASIC VALIDATION
    # ======================================

    modules = module_text.split()


    # Prevent shell command injection.
    # Only allow normal Python package characters.

    for module in modules:

        if not all(

            char.isalnum()
            or char in "._-"

            for char in module

        ):

            await update.message.reply_text(

                "❌ Invalid module name.\n\n"
                "Please use only valid Python package names."

            )

            return WAITING_FOR_MODULE


    await update.message.reply_text(

        "⏳ Installing module(s)...\n\n"
        f"📦 `{module_text}`",

        parse_mode="Markdown"

    )


    results = []


    # ======================================
    # INSTALL EACH MODULE
    # ======================================

    for module in modules:

        try:

            process = subprocess.run(

                [

                    sys.executable,

                    "-m",

                    "pip",

                    "install",

                    module

                ],

                capture_output=True,

                text=True,

                timeout=120

            )


            if process.returncode == 0:

                results.append(

                    f"✅ `{module}` installed successfully."

                )

            else:

                error = (

                    process.stderr.strip()

                    or process.stdout.strip()

                    or "Unknown error"

                )


                if len(error) > 1000:

                    error = error[-1000:]


                results.append(

                    f"❌ `{module}` installation failed.\n\n"
                    f"```text\n{error}\n```"

                )


        except subprocess.TimeoutExpired:

            results.append(

                f"⏱️ `{module}` installation timed out."

            )


        except Exception as e:

            results.append(

                f"❌ Error installing `{module}`:\n"
                f"{str(e)}"

            )


    # ======================================
    # RESULT
    # ======================================

    keyboard = InlineKeyboardMarkup([

        [

            InlineKeyboardButton(

                "📦 Install More",

                callback_data="module_install"

            )

        ],

        [

            InlineKeyboardButton(

                "⬅️ Modules",

                callback_data="modules_menu"

            )

        ],

        [

            InlineKeyboardButton(

                "🏠 Back",

                callback_data="back_home"

            )

        ]

    ])


    await update.message.reply_text(

        "📦 Module Installation Result\n\n"

        + "\n\n".join(results),

        reply_markup=keyboard,

        parse_mode="Markdown"

    )


    return ConversationHandler.END


# ==========================================
# CANCEL MODULE INSTALLATION
# ==========================================

async def cancel_module(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:

        await query.answer()

        keyboard = InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "📦 Install Module",

                    callback_data="module_install"

                )

            ],

            [

                InlineKeyboardButton(

                    "⬅️ Back",

                    callback_data="back_home"

                )

            ]

        ])


        await query.edit_message_text(

            "📦 Module Manager\n\n"
            "Choose an option.",

            reply_markup=keyboard

        )


    return ConversationHandler.END


# ==========================================
# CONVERSATION HANDLER
# ==========================================

def get_module_conversation_handler():

    return ConversationHandler(

        entry_points=[

            CallbackQueryHandler(

                ask_module,

                pattern=r"^module_install$"

            )

        ],

        states={

            WAITING_FOR_MODULE: [

                MessageHandler(

                    filters.TEXT
                    & ~filters.COMMAND,

                    install_module

                )

            ]

        },

        fallbacks=[

            CallbackQueryHandler(

                cancel_module,

                pattern=r"^modules_menu$"

            ),

            CallbackQueryHandler(

                cancel_module,

                pattern=r"^back_home$"

            )

        ],

        per_user=True,

        per_chat=True,

        allow_reentry=True

    )