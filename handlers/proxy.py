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

async def ask_proxy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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

async def save_proxy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:

        return ConversationHandler.END


    proxy = (

        update.message.text or ""

    ).strip()


    if not proxy:

        await update.message.reply_text(

            "❌ Please send a valid proxy."

        )

        return WAITING_FOR_PROXY


    # ======================================
    # BASIC VALIDATION
    # ======================================

    if len(proxy) > 500:

        await update.message.reply_text(

            "❌ Proxy address is too long."

        )

        return WAITING_FOR_PROXY


    try:

        result = add_proxy(proxy)


        if result is False:

            await update.message.reply_text(

                "❌ Failed to add proxy.\n\n"
                "The proxy may already exist."

            )

            return ConversationHandler.END


        keyboard = InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "➕ Add Another",

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

                    "⬅️ Proxy Manager",

                    callback_data="proxy_panel"

                )

            ]

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

    query = update.callback_query

    await query.answer()


    try:

        proxies = get_proxies()


    except Exception as e:

        await query.edit_message_text(

            "❌ Could not load proxies.\n\n"
            f"{str(e)}",

            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(

                        "⬅️ Proxy Manager",

                        callback_data="proxy_panel"

                    )

                ]

            ])

        )

        return


    if not proxies:

        await query.edit_message_text(

            "📋 Proxy List\n\n"
            "No proxies have been added yet.",

            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(

                        "➕ Add Proxy",

                        callback_data="proxy_add"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "⬅️ Proxy Manager",

                        callback_data="proxy_panel"

                    )

                ]

            ])

        )

        return


    keyboard = []


    for index, proxy in enumerate(

        proxies,

        start=1

    ):

        if isinstance(proxy, dict):

            proxy_id = proxy.get(

                "id",

                index

            )

            proxy_value = proxy.get(

                "proxy",

                proxy.get(

                    "address",

                    str(proxy)

                )

            )

        else:

            try:

                proxy_id = proxy["id"]

                proxy_value = proxy["proxy"]

            except Exception:

                proxy_id = index

                proxy_value = str(proxy)


        # Keep button text short

        display_proxy = str(

            proxy_value

        )


        if len(display_proxy) > 35:

            display_proxy = (

                display_proxy[:32]

                + "..."

            )


        keyboard.append([

            InlineKeyboardButton(

                f"🌐 {display_proxy}",

                callback_data=(

                    f"proxy_delete|{proxy_id}"

                )

            )

        ])


    keyboard.append([

        InlineKeyboardButton(

            "➕ Add Proxy",

            callback_data="proxy_add"

        )

    ])


    keyboard.append([

        InlineKeyboardButton(

            "⬅️ Proxy Manager",

            callback_data="proxy_panel"

        )

    ])


    await query.edit_message_text(

        "📋 Proxy List\n\n"
        "Tap a proxy below to delete it.",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

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

        proxy_id = int(

            query.data.split(

                "|",

                1

            )[1]

        )


        result = delete_proxy(

            proxy_id

        )


        if result is False:

            await query.answer(

                "❌ Could not delete proxy.",

                show_alert=True

            )

            return


        await query.answer(

            "✅ Proxy deleted."

        )


        # Refresh list

        await show_proxies(

            update,

            context

        )


    except Exception as e:

        await query.answer(

            f"❌ Error: {str(e)}",

            show_alert=True

        )


# ==========================================
# CANCEL
# ==========================================

async def cancel_proxy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:

        await query.answer()

        await proxy_panel(

            update,

            context

        )


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

                    filters.TEXT
                    & ~filters.COMMAND,

                    save_proxy

                )

            ]

        },

        fallbacks=[

            CallbackQueryHandler(

                cancel_proxy,

                pattern=r"^proxy_panel$"

            ),

            CallbackQueryHandler(

                cancel_proxy,

                pattern=r"^back_home$"

            )

        ],

        per_user=True,

        per_chat=True,

        allow_reentry=True

    )