# bot.py

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==========================================
# CONFIG
# ==========================================

from config import BOT_TOKEN


# ==========================================
# DATABASE
# ==========================================

from database import init_database


# ==========================================
# START
# ==========================================

from handlers.start import start


# ==========================================
# UPLOAD
# ==========================================

from handlers.upload import upload_file


# ==========================================
# INPUT
# ==========================================

from handlers.input import (
    input_handler,
    get_input_conversation_handler,
)


# ==========================================
# MODULES
# ==========================================

from handlers.modules import (
    modules_panel,
    add_module,
    remove_module,
    show_modules,
    get_module_conversation_handler,
)


# ==========================================
# PROXY
# ==========================================

from handlers.proxy import (
    proxy_panel,
    show_proxies,
    delete_proxy_callback,
    get_proxy_conversation_handler,
    use_proxy_panel,
    assign_proxy_callback,
)


# ==========================================
# MY FILES
# ==========================================

from handlers.my_files import (
    my_files,
    file_view,
    start_file,
    stop_file,
    restart_file,
    logs_file,
    delete_user_file,
    confirm_delete_file,
)


# ==========================================
# ADMIN
# ==========================================

from handlers.admin import (
    admin_panel,
    show_pending,
    admin_user,
    approve_user,
    block_user,
    reject_user,
    show_approved,
    show_blocked,
)


# ==========================================
# CALLBACK
# ==========================================

from handlers.callback import (
    handle_callback,
    back_home_handler,
)


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(

    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),

    level=logging.INFO

)

logger = logging.getLogger(__name__)


# ==========================================
# ERROR HANDLER
# ==========================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(

        "❌ Error while processing update: %s",

        context.error

    )


# ==========================================
# MAIN
# ==========================================

async def main():

    # ======================================
    # DATABASE
    # ======================================

    print(
        "🔄 Initializing database..."
    )

    init_database()


    # ======================================
    # TELEGRAM APPLICATION
    # ======================================

    print(
        "🔄 Connecting to Telegram..."
    )


    application = (

        Application.builder()

        .token(BOT_TOKEN)

        .build()

    )


    # ======================================
    # START COMMAND
    # ======================================

    application.add_handler(

        CommandHandler(

            "start",

            start

        )

    )


    # ======================================
    # UPLOAD DOCUMENT
    # ======================================

    application.add_handler(

        MessageHandler(

            filters.Document.ALL,

            upload_file

        )

    )


    # ======================================
    # MY FILES
    # ======================================

    application.add_handler(

        CallbackQueryHandler(

            my_files,

            pattern=r"^my_files$"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            file_view,

            pattern=r"^file_view\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            start_file,

            pattern=r"^start_file\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            stop_file,

            pattern=r"^stop_file\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            restart_file,

            pattern=r"^restart_file\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            logs_file,

            pattern=r"^logs_file\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            delete_user_file,

            pattern=r"^delete_file\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            confirm_delete_file,

            pattern=r"^confirm_delete\|"

        )

    )


    # ======================================
    # PROXY MANAGER
    # ======================================

    application.add_handler(

        CallbackQueryHandler(

            proxy_panel,

            pattern=r"^proxy_panel$"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            show_proxies,

            pattern=r"^proxy_list$"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            delete_proxy_callback,

            pattern=r"^proxy_delete\|"

        )

    )


    # ======================================
    # PROXY CONVERSATION
    # ======================================

    application.add_handler(

        get_proxy_conversation_handler()

    )

    # Register use-proxy handlers
    application.add_handler(
        CallbackQueryHandler(
            use_proxy_panel,
            pattern=r"^proxy_use_panel\|"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            assign_proxy_callback,
            pattern=r"^proxy_assign\|"
        )
    )


    # ======================================
    # MODULES
    # ======================================

    application.add_handler(

        CallbackQueryHandler(

            modules_panel,

            pattern=r"^modules_panel(?:\|.+)?$"

        )

    )

    application.add_handler(

        get_module_conversation_handler()

    )


    application.add_handler(

        CallbackQueryHandler(

            show_modules,

            pattern=r"^modules_list$"

        )

    )


    # Note: module installation entrypoint is handled by the conversation handler


    # ======================================
    # INPUT
    # ======================================

    # Register the input conversation handler (replaces the simple CallbackQueryHandler)
    application.add_handler(
        get_input_conversation_handler()
    )


    # ======================================
    # ADMIN PANEL
    # ======================================

    application.add_handler(

        CallbackQueryHandler(

            admin_panel,

            pattern=r"^admin_panel$"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            show_pending,

            pattern=r"^admin_pending$"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            admin_user,

            pattern=r"^admin_user\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            approve_user,

            pattern=r"^admin_approve\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            block_user,

            pattern=r"^admin_block\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            reject_user,

            pattern=r"^admin_reject\|"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            show_approved,

            pattern=r"^admin_approved$"

        )

    )


    application.add_handler(

        CallbackQueryHandler(

            show_blocked,

            pattern=r"^admin_blocked$"

        )

    )


    # ======================================
    # GENERAL CALLBACK HANDLER
    # ======================================

    application.add_handler(

        CallbackQueryHandler(

            back_home_handler,

            pattern=r"^back_home$"

        )

    )

    application.add_handler(

        CallbackQueryHandler(

            handle_callback

        )

    )


    # ======================================
    # ERROR HANDLER
    # ======================================

    application.add_error_handler(

        error_handler

    )


    # ======================================
    # START BOT
    # ======================================

    print(
        "✅ Connected to Telegram!"
    )

    print(
        "🚀 Bot is running successfully!"
    )

    print(
        "Press Ctrl+C to stop."
    )


    try:

        await application.initialize()

        await application.start()

        await application.updater.start_polling(

            drop_pending_updates=True

        )


        # Keep bot running

        while True:

            await asyncio.sleep(

                3600

            )


    except KeyboardInterrupt:

        print(

            "\n🛑 Stopping Bot..."

        )


    finally:

        try:

            if application.updater:

                await application.updater.stop()

        except Exception:

            pass


        try:

            await application.stop()

        except Exception:

            pass


        try:

            await application.shutdown()

        except Exception:

            pass


        print(

            "\n🛑 Stopping Bot..."

        )


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    try:

        asyncio.run(

            main()

        )

    except KeyboardInterrupt:

        print(

            "\n🛑 Bot stopped by Uday Kashyap."

        )
