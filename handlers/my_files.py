# handlers/my_files.py

import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.error import BadRequest

from telegram.ext import ContextTypes

from database import (
    get_user_files,
    delete_file,
)

from core.process import (
    start_process,
    stop_process,
    restart_process,
    get_logs,
    is_running,
)


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
# FILE OWNER CHECK
# ==========================================
def get_file_value(
    file,
    key,
    default=None
):
    try:
        if isinstance(file, dict):
            return file.get(key, default)
        return file[key]
    except Exception:
        return default


# ==========================================
# MY FILES
# ==========================================
async def my_files(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        if not update.effective_user:
            return
        user_id = update.effective_user.id

    try:
        files = get_user_files(user_id)
    except Exception as e:
        if query:
            await safe_edit(
                query,
                "❌ Could not load your files.\n\n"
                f"Error: {e}",
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

    if not files:
        text = (
            "📁 My Files\n\n"
            "You haven't uploaded any files yet.\n\n"
            "Upload a Python file to see it here."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Upload File", callback_data="upload_file")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_home")]
        ])
        if query:
            await safe_edit(query, text, keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
        return

    keyboard = []
    for file in files:
        filename = get_file_value(file, "filename", "")
        if not filename:
            continue
        try:
            running = is_running(filename)
        except Exception:
            running = False
        status = "🟢 Running" if running else "🔴 Stopped"
        keyboard.append([
            InlineKeyboardButton(
                f"📄 {filename} • {status}",
                callback_data=(f"file_view|{filename}")
            )
        ])

    keyboard.append([InlineKeyboardButton("📤 Upload File", callback_data="upload_file")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_home")])

    text = (
        "📁 My Files\n\n"
        "Here are your uploaded files.\n"
        "Select a file to manage it."
    )

    if query:
        await safe_edit(query, text, InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ==========================================
# FILE DETAILS
# ==========================================
async def file_view(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    filename = query.data.split("|", 1)[1]

    try:
        files = get_user_files(user_id)
    except Exception:
        await query.answer("❌ Could not verify file ownership.", show_alert=True)
        return

    user_file = None
    for file in files:
        current_filename = get_file_value(file, "filename", "")
        if current_filename == filename:
            user_file = file
            break

    if user_file is None:
        await query.answer("❌ You don't have access to this file.", show_alert=True)
        return

    context.user_data["active_file"] = filename

    try:
        running = is_running(filename)
    except Exception:
        running = False

    context.user_data["active_file_running"] = running
    status = "🟢 Running" if running else "🔴 Stopped"

    upload_date = (
        get_file_value(user_file, "uploaded_at", None)
        or get_file_value(user_file, "created_at", None)
        or "Unknown"
    )

    text = (
        "📄 File Details\n\n"
        f"📌 Filename: `{filename}`\n"
        f"📊 Status: {status}\n"
        f"📅 Uploaded: {upload_date}\n\n"
        "Choose an action:"
    )

    # Buttons
    if running:
        keyboard = [
            [
                InlineKeyboardButton("⏹️ Stop", callback_data=(f"stop_file|{filename}")),
                InlineKeyboardButton("🔄 Restart", callback_data=(f"restart_file|{filename}")),
            ],
            [
                InlineKeyboardButton("📜 Logs", callback_data=(f"logs_file|{filename}")),
                InlineKeyboardButton("⌨️ Input", callback_data=f"input_file|{filename}"),
            ],
            [
                InlineKeyboardButton("🌐 Use Proxy", callback_data=(f"proxy_use_panel|{filename}")),
            ],
            [
                InlineKeyboardButton("📦 Modules", callback_data=f"modules_panel|{filename}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=(f"delete_file|{filename}")),
            ],
            [InlineKeyboardButton("⬅️ My Files", callback_data="my_files")],
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("▶️ Start", callback_data=(f"start_file|{filename}")),
                InlineKeyboardButton("🔄 Restart", callback_data=(f"restart_file|{filename}")),
            ],
            [
                InlineKeyboardButton("📜 Logs", callback_data=(f"logs_file|{filename}")),
                InlineKeyboardButton("⌨️ Input", callback_data=f"input_file|{filename}"),
            ],
            [
                InlineKeyboardButton("🌐 Use Proxy", callback_data=(f"proxy_use_panel|{filename}")),
            ],
            [
                InlineKeyboardButton("📦 Modules", callback_data=f"modules_panel|{filename}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=(f"delete_file|{filename}")),
            ],
            [InlineKeyboardButton("⬅️ My Files", callback_data="my_files")],
        ]

    await safe_edit(query, text, InlineKeyboardMarkup(keyboard))


# ==========================================
# DELETE FILE
# ==========================================
async def delete_user_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    filename = query.data.split("|", 1)[1]

    try:
        files = get_user_files(user_id)
    except Exception:
        await query.answer("❌ Could not verify file ownership.", show_alert=True)
        return

    owns_file = False
    for file in files:
        current_filename = get_file_value(file, "filename", "")
        if current_filename == filename:
            owns_file = True
            break

    if not owns_file:
        await query.answer("❌ You don't have access to this file.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=(f"confirm_delete|{filename}")),
            InlineKeyboardButton("❌ Cancel", callback_data=(f"file_view|{filename}")),
        ]
    ])

    await safe_edit(query, "⚠️ Delete File?\n\n" f"📄 `{filename}`\n\n" "This will remove the file from your account.", keyboard)


# ==========================================
# CONFIRM DELETE
# ==========================================
async def confirm_delete_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    filename = query.data.split("|", 1)[1]

    try:
        files = get_user_files(user_id)
    except Exception:
        await query.answer("❌ Could not verify file ownership.", show_alert=True)
        return

    owns_file = any(
        get_file_value(file, "filename", "") == filename
        for file in files
    )

    if not owns_file:
        await query.answer("❌ You don't have access to this file.", show_alert=True)
        return

    try:
        if is_running(filename):
            stop_process(filename)
    except Exception:
        pass

    try:
        result = delete_file(user_id, filename)
        if result is False:
            await query.answer("❌ Could not delete file.", show_alert=True)
            return
    except Exception as e:
        await query.answer(f"❌ Delete failed: {e}", show_alert=True)
        return

    filepath = os.path.join("uploads", filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

    logpath = os.path.join("logs", filename + ".log")
    try:
        if os.path.exists(logpath):
            os.remove(logpath)
    except Exception:
        pass

    await query.answer("✅ File deleted successfully.")
    await my_files(update, context)


# ==========================================
# START FILE
# ==========================================
async def start_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    filename = query.data.split("|", 1)[1]

    file_path = None
    for file in get_user_files(query.from_user.id):
        if get_file_value(file, "filename", "") == filename:
            file_path = get_file_value(file, "file_path", "")
            break

    success, message = start_process(filename, file_path=file_path or None)
    context.user_data["active_file"] = filename
    context.user_data["active_file_running"] = success

    await query.answer(message, show_alert=not success)
    await file_view(update, context)


# ==========================================
# STOP FILE
# ==========================================
async def stop_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    filename = query.data.split("|", 1)[1]
    success, message = stop_process(filename)
    context.user_data["active_file"] = filename
    context.user_data["active_file_running"] = False
    await query.answer(message, show_alert=not success)
    await file_view(update, context)


# ==========================================
# RESTART FILE
# ==========================================
async def restart_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    filename = query.data.split("|", 1)[1]
    success, message = restart_process(filename)
    context.user_data["active_file"] = filename
    context.user_data["active_file_running"] = success
    await query.answer(message, show_alert=not success)
    await file_view(update, context)


# ==========================================
# SHOW LOGS
# ==========================================
async def logs_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    filename = query.data.split("|", 1)[1]
    logs = get_logs(filename)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=(f"file_view|{filename}"))]])
    await safe_edit(query, f"📜 Logs for `{filename}`\n\n```text\n{logs}\n```", keyboard)
