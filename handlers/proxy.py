# handlers/proxy.py

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

from database import (
    add_proxy,
    get_proxies,
    delete_proxy,
)
from core.auth import is_admin

# ==========================================
# CONVERSATION STATE
# ==========================================
WAITING_FOR_PROXY = 1

# ==========================================
# PROXY MANAGER MENU
# ==========================================
async def proxy_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    if query:
        await query.answer()
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "➕ Add Proxy",
                    callback_data="proxy_add"
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 View Proxies",
                    callback_data="proxy_list"
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
            "🌐 Proxy Manager\n\n"
            "Manage proxies available for the bot.\n\n"
            "You can add a proxy and view or delete "
            "existing proxies.",
            reply_markup=keyboard
        )

# ==========================================
# ASK FOR PROXY
# ==========================================
async def ask_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌐 Add Proxy\n\n"
        "Send the proxy in one of these formats:\n\n"
        "• `IP:PORT`\n"
        "• `USER:PASS@IP:PORT`\n"
        "• `http://IP:PORT`\n"
        "• `http://USER:PASS@IP:PORT`\n\n"
        "Example:\n"
        "`127.0.0.1:8080`",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="proxy_panel"
                )
            ]
        ]),
        parse_mode="Markdown"
    )
    return WAITING_FOR_PROXY

# ==========================================
# ADD PROXY
# ==========================================
async def save_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return ConversationHandler.END

    proxy = (update.message.text or "").strip()
    if not proxy:
        await update.message.reply_text("❌ Please send a valid proxy.")
        return WAITING_FOR_PROXY

    if len(proxy) > 500:
        await update.message.reply_text("❌ Proxy address is too long.")
        return WAITING_FOR_PROXY

    try:
        # Save owner as the user who added the proxy
        user_id = update.message.from_user.id
        result = add_proxy(user_id, proxy)

        if result is False:
            await update.message.reply_text(
                "❌ Failed to add proxy.\n\n"
                "The proxy may already exist."
            )
            return ConversationHandler.END

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Another", callback_data="proxy_add")],
            [InlineKeyboardButton("📋 View Proxies", callback_data="proxy_list")],
            [InlineKeyboardButton("⬅️ Proxy Manager", callback_data="proxy_panel")]
        ])

        await update.message.reply_text(
            "✅ Proxy added successfully!\n\n"
            f"🌐 Proxy: `{proxy}`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ Error while adding proxy.\n\n"
            f"{str(e)}"
        )

    return ConversationHandler.END

# ==========================================
# SHOW PROXY LIST
# ==========================================
async def show_proxies(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Displays proxies. If context.user_data.get('proxy_target') is set,
    the list is rendered in 'assign' mode where buttons assign a proxy to that file.
    Otherwise it shows delete buttons (only for owners/admins).
    """
    query = update.callback_query
    await query.answer()

    try:
        proxies = get_proxies()  # returns list of rows with user_id, id, proxy, created_at
    except Exception as e:
        await query.edit_message_text(
            "❌ Could not load proxies.\n\n"
            f"{str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Proxy Manager", callback_data="proxy_panel")]
            ])
        )
        return

    assign_target = context.user_data.get("proxy_target")
    user_id = query.from_user.id
    user_is_admin = is_admin(user_id)

    # Filter proxies for non-admins: show only their own
    filtered = []
    for p in proxies:
        try:
            owner = p["user_id"]
        except Exception:
            # fallback when p is not a Row
            try:
                owner = p[1]
            except Exception:
                owner = None
        if user_is_admin or owner == user_id:
            filtered.append(p)
        elif assign_target:
            # if assign(context) and user isn't admin and not owner, don't show
            continue

    if not filtered:
        await query.edit_message_text(
            "📋 Proxy List\n\n"
            "No proxies available for you.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Proxy", callback_data="proxy_add")],
                [InlineKeyboardButton("⬅️ Proxy Manager", callback_data="proxy_panel")]
            ])
        )
        return

    keyboard = []
    for index, proxy in enumerate(filtered, start=1):
        if isinstance(proxy, dict) or hasattr(proxy, "keys"):
            proxy_id = proxy.get("id", index)
            proxy_value = proxy.get("proxy", str(proxy))
            owner = proxy.get("user_id", 0)
        else:
            # sqlite Row or tuple fallback
            try:
                proxy_id = proxy[0] if len(proxy) > 0 else index
                proxy_value = proxy[2] if len(proxy) > 2 else str(proxy)
                owner = proxy[1] if len(proxy) > 1 else 0
            except Exception:
                proxy_id = index
                proxy_value = str(proxy)
                owner = 0

        display_proxy = str(proxy_value)
        if len(display_proxy) > 35:
            display_proxy = display_proxy[:32] + "..."

        if assign_target:
            # show assign buttons to the user (only allowed if owner or admin)
            if user_is_admin or owner == user_id:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🌐 {display_proxy}",
                        callback_data=f"proxy_assign|{proxy_id}"
                    )
                ])
        else:
            # normal listing: show delete button only for owner/admin; otherwise show masked info (owner cannot delete)
            if user_is_admin or owner == user_id:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🌐 {display_proxy}",
                        callback_data=f"proxy_delete|{proxy_id}"
                    )
                ])
            else:
                # non-owner sees read-only entry without deletion
                keyboard.append([
                    InlineKeyboardButton(
                        f"🌐 {display_proxy}",
                        callback_data="proxy_panel"
                    )
                ])

    # add bottom controls
    keyboard.append([InlineKeyboardButton("➕ Add Proxy", callback_data="proxy_add")])
    keyboard.append([InlineKeyboardButton("⬅️ Proxy Manager", callback_data="proxy_panel")])

    await query.edit_message_text(
        "📋 Proxy List\n\n"
        ("Tap a proxy below to assign it to the active file." if assign_target else "Tap a proxy below to manage it."),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================
# DELETE PROXY
# ==========================================
async def delete_proxy_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    try:
        proxy_id = int(query.data.split("|", 1)[1])
    except Exception as e:
        await query.answer(f"❌ Error: {e}", show_alert=True)
        return

    # Check ownership or admin privileges
    user_id = query.from_user.id
    user_is_admin = is_admin(user_id)

    # Find proxy owner
    proxies = get_proxies()
    owner_id = None
    for p in proxies:
        try:
            if p[0] == proxy_id or (hasattr(p, 'keys') and p.get('id') == proxy_id):
                # tuple or row or dict
                owner_id = p[1] if not hasattr(p, 'keys') else p.get('user_id')
                break
        except Exception:
            pass

    if not user_is_admin and owner_id is not None and owner_id != user_id:
        await query.answer("❌ You don't have permission to delete this proxy.", show_alert=True)
        return

    try:
        result = delete_proxy(proxy_id)
        if result is False:
            await query.answer("❌ Could not delete proxy.", show_alert=True)
            return

        await query.answer("✅ Proxy deleted.")
        # Refresh list
        await show_proxies(update, context)
    except Exception as e:
        await query.answer(f"❌ Error: {str(e)}", show_alert=True)


# ==========================================
# ASSIGN/USE PROXY FLOW
# ==========================================
async def use_proxy_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point when user selects 'Use Proxy' for a file.
    Callback data should be: proxy_use_panel|<filename>
    """
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    parts = data.split("|", 1)
    if len(parts) > 1:
        filename = parts[1]
        context.user_data["proxy_target"] = filename
    else:
        context.user_data.pop("proxy_target", None)

    # Reuse show_proxies but in 'assign' mode
    await show_proxies(update, context)


async def assign_proxy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    callback_data: proxy_assign|<id>
    Uses context.user_data['proxy_target'] to find which file to apply the proxy to.
    """
    query = update.callback_query
    await query.answer()

    try:
        proxy_id = int(query.data.split("|", 1)[1])
    except Exception as e:
        await query.answer(f"❌ Error: {e}", show_alert=True)
        return

    filename = context.user_data.get("proxy_target")
    if not filename:
        await query.answer("❌ No target file selected.", show_alert=True)
        return

    # Load the proxy text
    proxies = get_proxies()
    proxy_text = None
    owner_id = None
    for p in proxies:
        try:
            if (hasattr(p, 'keys') and p.get('id') == proxy_id) or (not hasattr(p, 'keys') and p[0] == proxy_id):
                proxy_text = p[2] if not hasattr(p, 'keys') else p.get('proxy')
                owner_id = p[1] if not hasattr(p, 'keys') else p.get('user_id')
                break
        except Exception:
            pass

    if proxy_text is None:
        await query.answer("❌ Proxy not found.", show_alert=True)
        return

    # Permission check: only owner or admin can assign for the file
    user_id = query.from_user.id
    user_is_admin = is_admin(user_id)
    if not user_is_admin and owner_id != user_id:
        await query.answer("❌ You don't have permission to assign this proxy.", show_alert=True)
        return

    # Restart the process with the proxy (this uses core.process.restart_process with proxy)
    from core.process import restart_process
    try:
        success, message = restart_process(filename, proxy=proxy_text)
        await query.answer(message, show_alert=not success)
    except Exception as e:
        await query.answer(f"❌ Error: {e}", show_alert=True)

    # Clear target and return to file view or proxy list
    context.user_data.pop("proxy_target", None)
    try:
        await query.edit_message_text(f"✅ Proxy assigned to `{filename}`.\n\n{message}", parse_mode="Markdown")
    except Exception:
        pass


# ==========================================
# CANCEL
# ==========================================
async def cancel_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await proxy_panel(update, context)
    return ConversationHandler.END


# ==========================================
# CONVERSATION HANDLER
# ==========================================
def get_proxy_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                ask_proxy,
                pattern=r"^proxy_add$"
            )
        ],
        states={
            WAITING_FOR_PROXY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    save_proxy
                )
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_proxy, pattern=r"^proxy_panel$"),
            CallbackQueryHandler(cancel_proxy, pattern=r"^back_home$")
        ],
        per_user=True,
        per_chat=True,
        allow_reentry=True
    )
