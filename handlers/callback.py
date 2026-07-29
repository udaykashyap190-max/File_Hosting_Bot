
# handlers/callback.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.error import BadRequest

from telegram.ext import ContextTypes

from core.process import (
    start_process,
    stop_process,
    restart_process,
    get_logs,
    is_running
)


# ==========================================
# MAIN KEYBOARD
# ==========================================

def main_keyboard():

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
# SAFE EDIT
# ==========================================

async def safe_edit(
    query,
    text,
    reply_markup=None
):

    try:

        await query.edit_message_text(

            text=text,

            reply_markup=reply_markup

        )

    except BadRequest as e:

        if "Message is not modified" in str(e):

            return

        raise


# ==========================================
# BACK HOME HANDLER
# ==========================================

async def back_home_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query is None:
        return

    try:
        await query.answer()
    except Exception:
        pass

    await safe_edit(

        query,

        "🏠 Main Menu\n\n"
        "Choose an option:",

        main_keyboard()

    )


# ==========================================
# FILE CONTROL KEYBOARD
# ==========================================

def file_control_keyboard(
    filename,
    running=False
):

    buttons = []

    if running:

        buttons.append([

            InlineKeyboardButton(
                "⏹️ Stop",
                callback_data=
                f"stop_file|{filename}"
            ),

            InlineKeyboardButton(
                "🔄 Restart",
                callback_data=
                f"restart_file|{filename}"
            )

        ])

    else:

        buttons.append([

            InlineKeyboardButton(
                "▶️ Start",
                callback_data=
                f"start_file|{filename}"
            ),

            InlineKeyboardButton(
                "🔄 Restart",
                callback_data=
                f"restart_file|{filename}"
            )

        ])

    buttons.append([

        InlineKeyboardButton(
            "📜 Logs",
            callback_data=
            f"logs_file|{filename}"
        )

    ])

    buttons.append([

        InlineKeyboardButton(
            "⬅️ My Files",
            callback_data="my_files"
        )

    ])

    return InlineKeyboardMarkup(
        buttons
    )


# ==========================================
# CALLBACK HANDLER
# ==========================================

async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    user_id = query.from_user.id


    # ======================================
    # ANSWER CALLBACK
    # ======================================

    try:

        await query.answer()

    except Exception:

        pass


    # ======================================
    # UPLOAD FILE
    # ======================================

    if data == "upload_file":

        await safe_edit(

            query,

            "📤 Upload File\n\n"
            "Please send your Python `.py` file "
            "in this chat.\n\n"
            "After uploading, the file will be "
            "available in your My Files section.",

            InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="back_home"
                    )

                ]

            ])

        )

        return


    # ======================================
    # INPUT PANEL
    # ======================================

    if data == "input_panel":

        await safe_edit(

            query,

            "⌨️ Input Manager\n\n"
            "First start a file from My Files.\n\n"
            "When the running file asks for "
            "input, send your answer here.",

            InlineKeyboardMarkup([

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

        return


    # ======================================
    # MODULES PANEL
    # ======================================

    if data == "modules_panel":

        await safe_edit(

            query,

            "📦 Modules Manager\n\n"
            "Module manager is ready.\n\n"
            "You can add the module installation "
            "functionality in the Modules handler.",

            InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="back_home"
                    )

                ]

            ])

        )

        return


    # ======================================
    # PROXY PANEL
    # ======================================

    if data == "proxy_panel":

        await safe_edit(

            query,

            "🌐 Proxy Manager\n\n"
            "Use the Proxy Manager to manage "
            "your available proxies.",

            InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="back_home"
                    )

                ]

            ])

        )

        return


    # ======================================
    # MY FILES
    # ======================================

    if data == "my_files":

        # This callback should normally be handled
        # by handlers/my_files.py.

        return


    # ======================================
    # START FILE
    # ======================================

    if data.startswith(
        "start_file|"
    ):

        filename = data.split(
            "|",
            1
        )[1]

        success, message = start_process(
            filename
        )

        running = is_running(
            filename
        )

        await safe_edit(

            query,

            f"{message}\n\n"
            f"📄 File: `{filename}`",

            file_control_keyboard(
                filename,
                running
            )

        )

        return


    # ======================================
    # STOP FILE
    # ======================================

    if data.startswith(
        "stop_file|"
    ):

        filename = data.split(
            "|",
            1
        )[1]

        success, message = stop_process(
            filename
        )

        running = is_running(
            filename
        )

        await safe_edit(

            query,

            f"{message}\n\n"
            f"📄 File: `{filename}`",

            file_control_keyboard(
                filename,
                running
            )

        )

        return


    # ======================================
    # RESTART FILE
    # ======================================

    if data.startswith(
        "restart_file|"
    ):

        filename = data.split(
            "|",
            1
        )[1]

        success, message = restart_process(
            filename
        )

        running = is_running(
            filename
        )

        await safe_edit(

            query,

            f"{message}\n\n"
            f"📄 File: `{filename}`",

            file_control_keyboard(
                filename,
                running
            )

        )

        return


    # ======================================
    # SHOW LOGS
    # ======================================

    if data.startswith(
        "logs_file|"
    ):

        filename = data.split(
            "|",
            1
        )[1]

        logs = get_logs(
            filename
        )

        await safe_edit(

            query,

            f"📜 Logs for `{filename}`\n\n"
            f"```\n{logs}\n```",

            InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data=
                        f"file_view|{filename}"
                    )

                ]

            ])

        )

        return


    # ======================================
    # BACK HOME
    # ======================================

    if data == "back_home":

        await back_home_handler(update, context)

        return


    # ======================================
    # ADMIN PANEL
    # ======================================

    if data == "admin_panel":

        # handlers/admin.py should handle
        # the actual admin panel.

        return


    # ======================================
    # UNKNOWN CALLBACK
    # ======================================

    await query.answer(

        "⚠️ This button is not connected yet.",

        show_alert=True

    )
