from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.error import BadRequest

from telegram.ext import ContextTypes

from config import ADMIN_ID

from database import (
    get_pending_users,
    get_approved_users,
    get_blocked_users,
    set_user_status,
)


# ==========================================
# ADMIN CHECK
# ==========================================

def is_admin(user_id):

    try:
        return int(user_id) == int(ADMIN_ID)

    except Exception:
        return False


# ==========================================
# SAFE ROW VALUE
# Works with sqlite3.Row
# ==========================================

def row_value(row, key, default=""):

    try:

        value = row[key]

        if value is None:

            return default

        return value

    except (KeyError, IndexError):

        return default


# ==========================================
# SAFE EDIT
# ==========================================

async def safe_edit(
    query,
    text,
    reply_markup=None,
):

    try:

        await query.edit_message_text(

            text=text,

            reply_markup=reply_markup,

            parse_mode="Markdown",

        )

    except BadRequest as e:

        if "Message is not modified" in str(e):

            return

        raise


# ==========================================
# ADMIN PANEL
# ==========================================

async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True,

        )

        return


    await query.answer()


    keyboard = InlineKeyboardMarkup([

        [

            InlineKeyboardButton(

                "⏳ Pending Users",

                callback_data="admin_pending",

            )

        ],

        [

            InlineKeyboardButton(

                "✅ Approved Users",

                callback_data="admin_approved",

            )

        ],

        [

            InlineKeyboardButton(

                "🚫 Blocked Users",

                callback_data="admin_blocked",

            )

        ],

        [

            InlineKeyboardButton(

                "⬅️ Back",

                callback_data="back_home",

            )

        ],

    ])


    await safe_edit(

        query,

        "👑 *Admin Panel*\n\n"
        "Manage users who can access the bot.",

        keyboard,

    )


# ==========================================
# PENDING USERS
# ==========================================

async def show_pending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True,

        )

        return


    await query.answer()


    users = get_pending_users()


    buttons = []


    for user in users:

        user_id = int(

            row_value(

                user,

                "user_id",

                0,

            )

        )


        name = (

            row_value(

                user,

                "first_name",

            )

            or row_value(

                user,

                "username",

            )

            or str(user_id)

        )


        buttons.append([

            InlineKeyboardButton(

                f"👤 {name}",

                callback_data=(

                    f"admin_user|{user_id}"

                ),

            )

        ])


    if buttons:

        text = (

            "⏳ *Pending Users*\n\n"

            "Select a user to manage:"

        )

    else:

        text = (

            "⏳ *Pending Users*\n\n"

            "No pending users."

        )


    buttons.append([

        InlineKeyboardButton(

            "⬅️ Admin Panel",

            callback_data="admin_panel",

        )

    ])


    await safe_edit(

        query,

        text,

        InlineKeyboardMarkup(

            buttons

        ),

    )


# ==========================================
# USER ACTION MENU
# ==========================================

async def admin_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True,

        )

        return


    await query.answer()


    try:

        user_id = int(

            query.data.split(

                "|",

                1,

            )[1]

        )

    except (

        ValueError,

        IndexError,

    ):

        await query.answer(

            "❌ Invalid user.",

            show_alert=True,

        )

        return


    users = get_pending_users()


    selected_user = None


    for user in users:

        current_id = int(

            row_value(

                user,

                "user_id",

                0,

            )

        )


        if current_id == user_id:

            selected_user = user

            break


    if selected_user is None:

        await query.answer(

            "⚠️ User is no longer pending.",

            show_alert=True,

        )

        return


    name = (

        row_value(

            selected_user,

            "first_name",

        )

        or row_value(

            selected_user,

            "username",

        )

        or "Unknown"

    )


    username = row_value(

        selected_user,

        "username",

    )


    if username:

        username_text = f"@{username}"

    else:

        username_text = "Not available"


    keyboard = InlineKeyboardMarkup([

        [

            InlineKeyboardButton(

                "✅ Approve",

                callback_data=(

                    f"admin_approve|{user_id}"

                ),

            )

        ],

        [

            InlineKeyboardButton(

                "🚫 Block",

                callback_data=(

                    f"admin_block|{user_id}"

                ),

            ),

            InlineKeyboardButton(

                "❌ Reject",

                callback_data=(

                    f"admin_reject|{user_id}"

                ),

            ),

        ],

        [

            InlineKeyboardButton(

                "⬅️ Pending Users",

                callback_data="admin_pending",

            )

        ],

    ])


    text = (

        "👤 *User Details*\n\n"

        f"Name: {name}\n"

        f"Username: {username_text}\n"

        f"User ID: `{user_id}`\n\n"

        "Choose an action:"

    )


    await safe_edit(

        query,

        text,

        keyboard,

    )


# ==========================================
# APPROVE USER
# ==========================================

async def approve_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True,

        )

        return


    try:

        user_id = int(

            query.data.split(

                "|",

                1,

            )[1]

        )

    except (

        ValueError,

        IndexError,

    ):

        await query.answer(

            "❌ Invalid user.",

            show_alert=True,

        )

        return


    set_user_status(

        user_id,

        "approved",

    )


    await query.answer(

        "✅ User approved.",

        show_alert=True,

    )


    await show_pending(

        update,

        context,

    )


# ==========================================
# BLOCK USER
# ==========================================

async def block_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True,

        )

        return


    try:

        user_id = int(

            query.data.split(

                "|",

                1,

            )[1]

        )

    except (

        ValueError,

        IndexError,

    ):

        await query.answer(

            "❌ Invalid user.",

            show_alert=True,

        )

        return


    set_user_status(

        user_id,

        "blocked",

    )


    await query.answer(

        "🚫 User blocked.",

        show_alert=True,

    )


    await show_pending(

        update,

        context,

    )


# ==========================================
# REJECT USER
# ==========================================

async def reject_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True,

        )

        return


    try:

        user_id = int(

            query.data.split(

                "|",

                1,

            )[1]

        )

    except (

        ValueError,

        IndexError,

    ):

        await query.answer(

            "❌ Invalid user.",

            show_alert=True,

        )

        return


    set_user_status(

        user_id,

        "blocked",

    )


    await query.answer(

        "❌ User rejected.",

        show_alert=True,

    )


    await show_pending(

        update,

        context,

    )


# ==========================================
# APPROVED USERS
# ==========================================

async def show_approved(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True,

        )

        return


    await query.answer()


    users = get_approved_users()


    lines = [

        "✅ *Approved Users*",

        "",

    ]


    for user in users:

        user_id = row_value(

            user,

            "user_id",

            "0",

        )


        name = (

            row_value(

                user,

                "first_name",

            )

            or row_value(

                user,

                "username",

            )

            or "Unknown"

        )


        lines.append(

            f"👤 {name} — `{user_id}`"

        )


    if len(lines) == 2:

        lines.append(

            "No approved users."

        )


    keyboard = InlineKeyboardMarkup([

        [

            InlineKeyboardButton(

                "⬅️ Admin Panel",

                callback_data="admin_panel",

            )

        ]

    ])


    await safe_edit(

        query,

        "\n".join(lines),

        keyboard,

    )


# ==========================================
# BLOCKED USERS
# ==========================================

async def show_blocked(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True,

        )

        return


    await query.answer()


    users = get_blocked_users()


    lines = [

        "🚫 *Blocked Users*",

        "",

    ]


    for user in users:

        user_id = row_value(

            user,

            "user_id",

            "0",

        )


        name = (

            row_value(

                user,

                "first_name",

            )

            or row_value(

                user,

                "username",

            )

            or "Unknown"

        )


        lines.append(

            f"👤 {name} — `{user_id}`"

        )


    if len(lines) == 2:

        lines.append(

            "No blocked users."

        )


    keyboard = InlineKeyboardMarkup([

        [

            InlineKeyboardButton(

                "⬅️ Admin Panel",

                callback_data="admin_panel",

            )

        ]

    ])


    await safe_edit(

        query,

        "\n".join(lines),

        keyboard,

    )
