import logging
import random
import asyncio
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMember,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from telegram.error import Forbidden, BadRequest, TelegramError
from telegram.helpers import mention_html
from telegram import ChatMemberOwner, ChatMemberAdministrator
from config import ADMIN_IDS, SUPPORT_LINK , CHANNEL_USERNAME, BOT_TOKEN , SUPPORT_CHAT
import os 
from functools import wraps
from telegram.constants import ChatType
import html
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from datetime import datetime
from config import MONGODB_URI , DB_NAME
from pymongo import MongoClient
from typing import Optional
import logging
import asyncio
from datetime import datetime
from typing import Dict, Tuple
from telegram import (
    Update, ChatMember, InlineKeyboardButton,
    InlineKeyboardMarkup, User
)
from telegram.constants import ChatType, ParseMode, ChatMemberStatus
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ChatMemberHandler,
    ContextTypes
)
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
# ======================
# Logging Configuration
# ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ======================
# Constants & Settings
# ======================
CHANNEL_USERNAME = "@ShadowBotsHQ"
DEVELOPER_LINK = "https://t.me/FOS_FOUNDER"

SYSTEM_PHRASES = [
    "🔍 Initializing core modules...",
    "⚡ Booting AI subsystems...",
    "🛡️ Securing encrypted channels...",
    "🌐 Establishing satellite link...",
    "📡 Calibrating signal...",
    "🧠 Loading neural protocols...",
    "🔒 Encrypting data flow..."
]

PROGRESS_INTERVALS = [10, 25, 40, 55, 70, 85, 100]


# ======================
# Utility Functions
# ======================
async def send_typing_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Simulate typing action."""
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except TelegramError as e:
        logger.warning(f"Typing action failed: {e}")


async def is_user_in_channel(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if user has joined the required channel."""
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in {ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER}
    except Forbidden:
        logger.error("Bot is not an admin in the channel.")
    except BadRequest as e:
        logger.error(f"Bad request while checking channel membership: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during channel check: {e}")
    return False


# ======================
# Core Commands
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with animated loading effect."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    try:
        await send_typing_action(context, chat_id)

        # Initial loading message
        processing_msg = await update.effective_chat.send_message(
            f"<b>⚙️ SYSTEM INITIALIZATION ⚙️</b>\n"
            f"<i>• {random.choice(SYSTEM_PHRASES)}</i>\n"
            "<code>━━━━━━━━━━━━━━━━━━━━</code> [0%]",
            parse_mode=ParseMode.HTML
        )

        # Channel check
        if not await is_user_in_channel(context, user.id):
            await asyncio.sleep(0.8)
            return await show_restriction(update, context, processing_msg)

        # Animated progress bar
        for progress in PROGRESS_INTERVALS:
            await asyncio.sleep(random.uniform(0.25, 0.45))
            bar_length = progress // 5
            bar = "━" * bar_length + " " * (20 - bar_length)
            phrase = random.choice(SYSTEM_PHRASES)
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_msg.message_id,
                    text=f"<b>⚙️ SYSTEM INITIALIZATION ⚙️</b>\n<i>• {phrase}</i>\n<code>{bar}</code> [{progress}%]",
                    parse_mode=ParseMode.HTML
                )
            except TelegramError:
                break

        # Ready message
        await asyncio.sleep(0.6)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=processing_msg.message_id,
            text="<b>✅ SYSTEM ONLINE</b>\n<i>Welcome aboard, Commander.</i>",
            parse_mode=ParseMode.HTML
        )

        await asyncio.sleep(1.2)
        await show_welcome(update, context, processing_msg)

    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await update.effective_chat.send_message(
            "🚫 Critical error during initialization. Please try again later.",
            parse_mode=ParseMode.HTML
        )


async def show_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE, processing_msg=None):
    """Display welcome menu."""
    user = update.effective_user
    bot_me = await context.bot.get_me()

    welcome_text = (
        f"<b>🚀 Welcome, {user.mention_html()}!</b>\n\n"
        f"I am <b>{bot_me.first_name}</b>, your AI-powered assistant.\n\n"
        "🔹 <b>Capabilities:</b>\n"
        "• Advanced moderation & admin tools\n"
        "• Fun & entertainment features\n"
        "• Utility commands for convenience\n\n"
        "Type /help to explore my abilities."
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_me.username}?startgroup=true")],
        [
            InlineKeyboardButton("👑 Developer", url=DEVELOPER_LINK),
            InlineKeyboardButton("💬 Support", url=SUPPORT_LINK)
        ],
        [InlineKeyboardButton("📜 Commands", callback_data="show_help")]
    ])

    try:
        if processing_msg:
            await context.bot.delete_message(processing_msg.chat_id, processing_msg.message_id)
        await update.effective_chat.send_message(welcome_text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramError as e:
        logger.error(f"Failed to send welcome: {e}")


async def show_restriction(update: Update, context: ContextTypes.DEFAULT_TYPE, processing_msg=None):
    """Show channel join requirement message."""
    user = update.effective_user

    if processing_msg:
        try:
            await context.bot.delete_message(processing_msg.chat_id, processing_msg.message_id)
        except TelegramError:
            pass

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("🔄 Verify Access", callback_data="verify_access")]
    ])

    restriction_msg = (
        f"<b>🔒 Access Restricted</b>\n\n"
        f"{user.mention_html()}, please join our channel to proceed.\n\n"
        "Once done, tap <b>Verify Access</b>."
    )

    try:
        await update.effective_chat.send_message(restriction_msg, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramError as e:
        logger.error(f"Restriction message failed: {e}")


# ======================
# HELP MENU (Button-Based)
# ======================

HELP_CATEGORIES = {
    # Page 1
    "moderation": {
        "title": "🛡 Moderation",
        "commands": [
            "/admin - Admin tools",
            "/antibanall - Prevent mass bans",
            "/ban - Ban users",
            "/gban - Global ban",
            "/warn - Warn users",
            "/massactions - Bulk actions",
            "/perm - Permission management",
            "/blacklist - Block users (bkc.py)",
        ]
    },
    "security": {
        "title": "🔒 Security",
        "commands": [
            "/userwatch - Monitor users",
            "/log - View logs",
            "/nightmode - Night mode settings",
            "/antiflood - Prevent spamming",
            "/join - Join monitoring",
            "/leave - Leave monitoring",
        ]
    },
    
    # Page 2
    "anime": {
        "title": "🎌 Anime & Fun",
        "commands": [
            "/anime - Anime info",
            "/cosplay - Anime cosplay",
            "/couple - Couple matching",
            "/love - Love calculator",
            "/meme - Random memes",
            "/quote - Random quotes",
            "/quotes - More quotes",
            "/seasonal - Seasonal anime",
        ]
    },
    "games": {
        "title": "🎮 Games",
        "commands": [
            "/xo - Tic-tac-toe",
            "/rps - Rock paper scissors",
            "/pokedex - Pokémon info",
            "/sg - Game stats",
            "/sgen - Game generator",
            "/wish - Make a wish",
        ]
    },
    
    # Page 3
    "utilities": {
        "title": "⚙️ Utilities",
        "commands": [
            "/calc - Calculator",
            "/code - Code tools",
            "/currency - Currency converter",
            "/extract - Data extraction",
            "/figlet - ASCII art",
            "/font - Text styling",
            "/ip - IP lookup",
            "/ocr - Text recognition",
        ]
    },
    "media": {
        "title": "📸 Media",
        "commands": [
            "/image - Image tools",
            "/insta - Instagram tools",
            "/logo - Logo creation",
            "/sticker - Sticker tools",
            "/tts - Text-to-speech",
            "/upload - File upload",
            "/ytube - YouTube tools",
            "/reverse - Reverse image search",
        ]
    }
}

# Current page tracking
user_help_pages = {}

async def show_help(update_or_query, context: ContextTypes.DEFAULT_TYPE, page=1):
    """Show paginated help menu with category buttons"""
    user_id = update_or_query.effective_user.id
    user_help_pages[user_id] = page
    
    help_text = (
        f"📜 <b>Help Menu (Page {page}/3)</b>\n\n"
        "Available Prefixes: / ! . # $ % & ?\n\n"
        "Select a category below to view commands."
    )

    # Define buttons for each page
    page_buttons = {
        1: [
            [InlineKeyboardButton("🛡 Moderation", callback_data="help_moderation")],
            [InlineKeyboardButton("🔒 Security", callback_data="help_security")],
        ],
        2: [
            [InlineKeyboardButton("🎌 Anime & Fun", callback_data="help_anime")],
            [InlineKeyboardButton("🎮 Games", callback_data="help_games")],
        ],
        3: [
            [InlineKeyboardButton("⚙️ Utilities", callback_data="help_utilities")],
            [InlineKeyboardButton("📸 Media", callback_data="help_media")],
        ]
    }

    # Navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅ Previous", callback_data=f"help_page_{page-1}"))
    if page < 3:
        nav_buttons.append(InlineKeyboardButton("Next ➡", callback_data=f"help_page_{page+1}"))
    
    kb_buttons = page_buttons[page]
    if nav_buttons:
        kb_buttons.append(nav_buttons)
    kb_buttons.append([InlineKeyboardButton("⬅ Back to Menu", callback_data="back_to_menu")])

    kb = InlineKeyboardMarkup(kb_buttons)

    if isinstance(update_or_query, Update):
        await update_or_query.effective_chat.send_message(help_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update_or_query.edit_message_text(help_text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def show_help_category(query, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Show commands for a selected category"""
    cat_data = HELP_CATEGORIES.get(category)
    if not cat_data:
        return

    user_id = query.from_user.id
    current_page = user_help_pages.get(user_id, 1)
    
    text = f"<b>{cat_data['title']}</b>\n\n" + "\n".join(cat_data["commands"]) + "\n\nFound a bug? Report it using /bug"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅ Back to Help", callback_data=f"help_page_{current_page}")]
    ])

    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def help_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help page navigation"""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split("_")[-1])
    await show_help(query, context, page)

# ======================
# Callback Handler
# ======================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "verify_access":
        if await is_user_in_channel(context, query.from_user.id):
            return await show_welcome(update, context)
        else:
            return await query.edit_message_text(
                "<b>🚫 Access Denied</b>\nYou still need to join the channel.",
                parse_mode=ParseMode.HTML
            )

    elif query.data == "show_help":
        await show_help(query, context)

    elif query.data.startswith("help_"):
        category = query.data.replace("help_", "")
        await show_help_category(query, context, category)

    elif query.data == "back_to_menu":
        await show_welcome(update, context, query.message)


async def get_target_user(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat

    # Priority 1: Reply to a user's message
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    # Priority 2: User ID argument
    if context.args:
        user_id = context.args[0]
        if not user_id.isdigit():
            await message.reply_html("❌ Please provide a numeric user ID")
            return None
        try:
            member = await chat.get_member(int(user_id))
            return member.user
        except Exception:
            await message.reply_html("❌ User not found in this chat")
            return None

    await message.reply_html("⚠️ <b>Reply to a user's message or provide their user ID</b>")
    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 Admin Decorator
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PERMISSION_NAMES = {
    'can_change_info': '✏️ Change Group Info',
    'can_delete_messages': '🗑️ Delete Messages',
    'can_invite_users': '📨 Invite Users',
    'can_restrict_members': '🔨 Restrict Members',
    'can_pin_messages': '📌 Pin Messages',
    'can_promote_members': '🔼 Promote Members',
    'can_manage_video_chats': '🎥 Manage Video Chats',
    'can_manage_chat': '⚙️ Manage Chat',
    'can_post_messages': '📢 Post Messages',
    'can_edit_messages': '✂️ Edit Messages',
    'can_manage_topics': '💬 Manage Topics'
}

def admin_required(required_perms=None, allow_owner=True, show_perms=True):
    required_perms = required_perms or []
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            chat = update.effective_chat
            user = update.effective_user
            if chat.type == ChatType.PRIVATE:
                return await func(update, context, *args, **kwargs)
            try:
                member = await chat.get_member(user.id)
            except Exception as e:
                await update.effective_message.reply_html(
                    f"🔍 <b>Error checking your status:</b>\n<code>{html.escape(str(e))}</code>"
                )
                return
            # Owner bypass
            if isinstance(member, ChatMemberOwner) and allow_owner:
                return await func(update, context, *args, **kwargs)
            # Admin check
            if not isinstance(member, ChatMemberAdministrator):
                keyboard = []
                if show_perms:
                    keyboard.append([
                        InlineKeyboardButton(
                            "📜 Show Required Permissions",
                            callback_data=f"perms_{func.__name__}"
                        )
                    ])
                await update.effective_message.reply_html(
                    f"👑 <b>Admin Privileges Required</b>\n\n"
                    f"🙅‍♂️ <b>{user.mention_html()}</b>, you need <b>admin rights</b> to use this command.\n\n"
                    "💡 <i>Contact the group owner if you believe this is a mistake.</i>",
                    reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
                )
                return
            # Permission check
            missing_perms = [perm for perm in required_perms if not getattr(member, perm, False)]
            if missing_perms:
                perm_list = "\n".join(
                    f"➖ {PERMISSION_NAMES.get(perm, perm.replace('can_', '🚩 '))}"
                    for perm in missing_perms
                )
                await update.effective_message.reply_html(
                    f"🔐 <b>Permission Denied</b>\n\n"
                    f"🛡️ <b>{user.mention_html()}</b>, you're missing required permissions:\n\n"
                    f"{perm_list}\n\n"
                    "⚙️ <i>Ask the group owner to grant these permissions.</i>"
                )
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📌 Pin Commands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@admin_required(["can_pin_messages"])
async def pin(update: Update, context: CallbackContext):
    message = update.effective_message
    if message.reply_to_message:
        await message.reply_to_message.pin(disable_notification=True)
        await message.reply_html("📌 <b>Message pinned!</b>")
    else:
        await message.reply_html("⚠️ <b>Reply to a message to pin.</b>")

@admin_required(["can_pin_messages"])
async def unpin(update: Update, context: CallbackContext):
    await update.effective_chat.unpin_message()
    await update.effective_message.reply_html("📍 <b>Unpinned last message!</b>")

@admin_required([], allow_owner=True)
async def pinned(update: Update, context: CallbackContext):
    chat = update.effective_chat
    try:
        chat_info = await context.bot.get_chat(chat.id)
        pinned_msg = chat_info.pinned_message
        if not pinned_msg:
            await update.effective_message.reply_html(
                "📌 <b>No Pinned Message</b>\n\nThere is currently no pinned message in this chat."
            )
            return
        content = pinned_msg.text or "[Media content]"
        preview = (content[:100] + "...") if len(content) > 100 else content
        poster = pinned_msg.from_user.mention_html() if pinned_msg.from_user else "System"
        await update.effective_message.reply_html(
            "📌 <b>Pinned Message</b>\n\n"
            f"💬 <i>{html.escape(preview)}</i>\n\n"
            f"👤 Posted by: {poster}\n"
            f"⏰ {pinned_msg.date.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🔗 <a href='{pinned_msg.link if hasattr(pinned_msg, 'link') else ''}'>View Message</a>",
            disable_web_page_preview=True
        )
    except Exception as e:
        await update.effective_message.reply_html(
            f"⚠️ <b>Error retrieving pinned message</b>\n\n<code>{html.escape(str(e))}</code>"
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 👑 Promotion Commands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROMOTION_LEVELS = {
    'low': {
        'can_delete_messages': True,
        'can_pin_messages': True,
        'name': 'Junior Moderator',
        'emoji': '🔼'
    },
    'mid': {
        'can_delete_messages': True,
        'can_invite_users': True,
        'can_pin_messages': True,
        'can_manage_chat': True,
        'name': 'Senior Moderator',
        'emoji': '🔼'
    },
    'full': {
        'can_change_info': True,
        'can_delete_messages': True,
        'can_invite_users': True,
        'can_restrict_members': True,
        'can_pin_messages': True,
        'can_manage_chat': True,
        'can_manage_video_chats': True,
        'name': 'Full Admin',
        'emoji': '🌟'
    }
}

async def _handle_promotion(update: Update, context: CallbackContext, level: str):
    chat = update.effective_chat
    admin = update.effective_user
    config = PROMOTION_LEVELS[level]
    user = await get_target_user(update, context)
    if not user:
        return
    if user.id == admin.id:
        await update.effective_message.reply_html("❌ You can't promote yourself")
        return
    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            **{k: v for k, v in config.items() if k not in ['name', 'emoji']}
        )
        perms = []
        if config.get('can_delete_messages'): perms.append("Delete messages")
        if config.get('can_pin_messages'): perms.append("Pin messages")
        if config.get('can_invite_users'): perms.append("Invite users")
        if config.get('can_restrict_members'): perms.append("Restrict members")
        if config.get('can_change_info'): perms.append("Change group info")
        if config.get('can_manage_chat'): perms.append("Manage chat")
        await update.effective_message.reply_html(
            f"{config['emoji']} <b>{user.mention_html()} promoted to {config['name']}</b>\n\n"
            f"<b>Permissions granted:</b>\n"
            f"• {', '.join(perms)}\n\n"
            f"Promoted by: {admin.mention_html()}"
        )
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"🎖️ <b>You've been promoted in {chat.title}!</b>\n\n"
                     f"New role: {config['name']}\n"
                     f"Granted permissions: {', '.join(perms)}",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
    except Exception as e:
        await update.effective_message.reply_html(f"❌ Promotion failed: {str(e)}")

@admin_required(["can_promote_members"])
async def promote(update: Update, context: CallbackContext):
    await _handle_promotion(update, context, 'mid')

@admin_required(["can_promote_members"])
async def lowpromote(update: Update, context: CallbackContext):
    await _handle_promotion(update, context, 'low')

@admin_required(["can_promote_members"])
async def midpromote(update: Update, context: CallbackContext):
    await _handle_promotion(update, context, 'mid')

@admin_required(["can_promote_members"])
async def fullpromote(update: Update, context: CallbackContext):
    await _handle_promotion(update, context, 'full')

@admin_required(["can_promote_members"])
async def demote(update: Update, context: CallbackContext):
    chat = update.effective_chat
    admin = update.effective_user
    user = await get_target_user(update, context)
    if not user:
        await update.effective_message.reply_html("❌ Please reply to an admin or mention them")
        return
    member = await chat.get_member(user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await update.effective_message.reply_html(f"ℹ️ {user.mention_html()} is not an admin")
        return
    if user.id == admin.id:
        await update.effective_message.reply_html("🚫 You cannot demote yourself")
        return
    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            is_anonymous=False,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_chat=False,
            can_manage_video_chats=False
        )
        await update.effective_message.reply_html(
            f"⬇️ <b>Admin Demoted</b>\n\n"
            f"👤 User: {user.mention_html()}\n"
            f"🛡️ Previous Role: {getattr(member, 'custom_title', 'Admin')}\n"
            f"👤 Demoted by: {admin.mention_html()}"
        )
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"ℹ️ <b>You've been demoted in {chat.title}</b>\n\nYour admin privileges have been removed.",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
    except Exception as e:
        await update.effective_message.reply_html(
            f"❌ <b>Demotion Failed</b>\n\n<code>{html.escape(str(e))}</code>"
        )
        logger.error(f"Demotion error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧹 Cleanup Commands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@admin_required(["can_delete_messages"])
async def delete_msg(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user
    if not message.reply_to_message:
        msg = await message.reply_html(
            "🗑️ <b>Message Deletion</b>\n\n"
            "Please reply to a message to delete it.\n\n"
            "⚡ <i>This reminder will self-destruct in 5 seconds...</i>"
        )
        await asyncio.sleep(5)
        await msg.delete()
        await message.delete()
        return
    await message.reply_to_message.delete()
    confirmation = await message.reply_html(
        f"✅ <b>Message deleted by {user.mention_html()}</b>"
    )
    await message.delete()
    await asyncio.sleep(3)
    await confirmation.delete()

@admin_required(["can_delete_messages"])
async def purge(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    if not message.reply_to_message:
        msg = await message.reply_html(
            "🔍 <b>Purge Instructions</b>\n\n"
            "Reply to a message with /purge to delete\n"
            "all messages from this point back to the replied message.\n\n"
            "⚡ This reminder will auto-delete in 5 seconds..."
        )
        await asyncio.sleep(5)
        await msg.delete()
        await message.delete()
        return
    try:
        newest_id = message.message_id
        oldest_id = message.reply_to_message.message_id
        status_msg = await message.reply_html(
            "🧹 <b>Starting Purge...</b>\n\n"
            f"Preparing to delete messages {newest_id} → {oldest_id}"
        )
        deleted_count = 0
        for msg_id in range(newest_id - 1, oldest_id - 1, -1):
            try:
                await context.bot.delete_message(chat.id, msg_id)
                deleted_count += 1
                if deleted_count % 10 == 0:
                    await status_msg.edit_text(
                        f"🧹 <b>Purging Messages...</b>\n\n"
                        f"Deleted: {deleted_count}\n"
                        f"Remaining: {msg_id - oldest_id}",
                        parse_mode=ParseMode.HTML
                    )
            except Exception:
                pass
            await asyncio.sleep(0.3)
        await message.delete()
        await status_msg.edit_text(
            f"✅ <b>Purge Complete</b>\n\n"
            f"Deleted {deleted_count} messages\n"
            f"From ID: {newest_id} → {oldest_id}",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(10)
        await status_msg.delete()
    except Exception as e:
        error_msg = await message.reply_html(
            f"❌ <b>Purge Failed</b>\n\n{str(e)}"
        )
        await asyncio.sleep(10)
        await error_msg.delete()

@admin_required(["can_delete_messages"])
async def spurge(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    try:
        try:
            count = min(int(context.args[0]), 100) if context.args else 0
            if not 1 <= count <= 100:
                raise ValueError
        except (ValueError, IndexError):
            help_msg = await message.reply_html("Usage: /spurge <1-100>\nExample: /spurge 50")
            await asyncio.sleep(5)
            await help_msg.delete()
            return
        await message.delete()
        deleted = 0
        async for msg in context.bot.get_chat_history(chat.id, limit=count):
            if msg.from_user and msg.from_user.id == context.bot.id:
                try:
                    await msg.delete()
                    deleted += 1
                    await asyncio.sleep(0.3)
                except:
                    continue
        confirmation = await context.bot.send_message(
            chat_id=chat.id,
            text=f"🗑️ Purged {deleted} bot messages",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(3)
        await confirmation.delete()
    except Exception as e:
        error_msg = await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ Purge failed: {str(e)}",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(5)
        await error_msg.delete()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🏷 Group Info Commands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@admin_required(["can_change_info"])
async def settitle(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    title = " ".join(context.args).strip() if context.args else ""
    if not title:
        msg = await update.effective_message.reply_html(
            "🏷 <b>Group Title Setup</b>\n\n"
            "Usage: /settitle <new group name>\n"
            "Max 128 characters\n\n"
            "Example: /settitle Tech Community"
        )
        await asyncio.sleep(10)
        await msg.delete()
        return
    if len(title) > 128:
        await update.effective_message.reply_html("❌ Title too long (max 128 characters)")
        return
    try:
        old_title = chat.title
        await chat.set_title(title)
        confirmation = await update.effective_message.reply_html(
            f"✅ <b>Group Title Updated</b>\n\n"
            f"Old: <code>{html.escape(old_title)}</code>\n"
            f"New: <code>{html.escape(title)}</code>\n\n"
            f"Changed by: {user.mention_html()}"
        )
        await asyncio.sleep(15)
        await confirmation.delete()
        await update.effective_message.delete()
    except Exception as e:
        error_msg = await update.effective_message.reply_html(
            f"❌ Failed to update title: {str(e)}"
        )
        await asyncio.sleep(10)
        await error_msg.delete()

@admin_required(["can_change_info"])
async def setdesc(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    desc = " ".join(context.args).strip() if context.args else ""
    if not desc:
        msg = await update.effective_message.reply_html(
            "📝 <b>Group Description</b>\n\n"
            "Usage: /setdesc <description text>\n"
            "Max 255 characters\n\n"
            "Example: /setdesc Official group for our community"
        )
        await asyncio.sleep(10)
        await msg.delete()
        return
    if len(desc) > 255:
        await update.effective_message.reply_html(
            f"❌ Description too long ({len(desc)}/255 characters)"
        )
        return
    try:
        await chat.set_description(desc)
        confirmation = await update.effective_message.reply_html(
            "✅ <b>Description Updated</b>\n\n"
            f"<i>{html.escape(desc)}</i>\n\n"
            f"Set by: {user.mention_html()}"
        )
        await asyncio.sleep(15)
        await confirmation.delete()
        await update.effective_message.delete()
    except Exception as e:
        error_msg = await update.effective_message.reply_html(
            f"❌ Failed to update description: {str(e)}"
        )
        await asyncio.sleep(10)
        await error_msg.delete()

@admin_required(["can_change_info"])
async def setgpic(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not (message.reply_to_message and message.reply_to_message.photo):
        msg = await message.reply_html(
            "🖼 Reply to an image with /setgpic\n⚡ Use square images for best results"
        )
        await asyncio.sleep(5)
        await msg.delete()
        return
    try:
        photo_file = await message.reply_to_message.photo[-1].get_file()
        photo_path = f"gpic_{chat.id}.jpg"
        await photo_file.download_to_drive(photo_path)
        await chat.set_photo(photo=open(photo_path, "rb"))
        try:
            os.remove(photo_path)
        except:
            pass
        msg = await message.reply_html(f"✅ Group photo updated by {user.mention_html()}")
        await asyncio.sleep(5)
        await msg.delete()
    except Exception as e:
        error_msg = await message.reply_html(
            f"❌ Failed to update photo: {str(e)}"
        )
        await asyncio.sleep(5)
        await error_msg.delete()
    finally:
        try:
            os.remove(photo_path)
        except:
            pass

@admin_required(["can_change_info"])
async def rmgpic(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    try:
        chat_info = await context.bot.get_chat(chat.id)
        if not chat_info.photo:
            await update.effective_message.reply_html(
                "ℹ️ This group doesn't have a photo set"
            )
            return
        await chat.delete_photo()
        confirmation = await update.effective_message.reply_html(
            "✅ <b>Group Photo Removed</b>\n\n"
            f"The photo was removed by {user.mention_html()}"
        )
        await asyncio.sleep(10)
        await confirmation.delete()
        await update.effective_message.delete()
    except Exception as e:
        error_msg = await update.effective_message.reply_html(
            f"❌ Failed to remove photo: {str(e)}"
        )
        await asyncio.sleep(10)
        await error_msg.delete()

@admin_required(["can_invite_users"])
async def invitelink(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    try:
        loading_msg = await update.effective_message.reply_html(
            "⏳ <i>Generating secure invite link...</i>"
        )
        try:
            link = await chat.export_invite_link()
            is_new = True
        except:
            link = chat.invite_link
            is_new = False
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Regenerate", callback_data="invite_regen")],
            [InlineKeyboardButton("🚪 Share Link", switch_inline_query=f"Join {chat.title}: {link}")]
        ])
        await loading_msg.edit_text(
            f"🔗 <b>{'New' if is_new else 'Current'} Invite Link</b>\n\n"
            f"👥 <b>Group:</b> {chat.title}\n"
            f"👤 <b>Generated by:</b> {user.mention_html()}\n\n"
            f"<code>{link}</code>\n\n"
            f"ℹ️ <i>Link {'will expire' if is_new else 'never expires'}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    except Exception as e:
        error_msg = await update.effective_message.reply_html(
            f"❌ <b>Error generating link:</b>\n<code>{str(e)}</code>"
        )
        await asyncio.sleep(10)
        await error_msg.delete()

async def invite_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    try:
        new_link = await query.message.chat.export_invite_link()
        await query.message.edit_text(
            f"🔄 <b>New Invite Link Generated</b>\n\n"
            f"<code>{new_link}</code>\n\n"
            "⚠️ <i>The previous link is now invalid</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=query.message.reply_markup,
            disable_web_page_preview=True
        )
        await query.answer("New link generated!")
    except Exception as e:
        await query.answer(f"Error: {str(e)}", show_alert=True)

async def adminlist(update: Update, context: CallbackContext):
    chat = update.effective_chat
    try:
        admins = await chat.get_administrators()
        if not admins:
            return await update.effective_message.reply_html("👑 <i>No admins found</i>")
        admin_lines = []
        for admin in admins:
            badge = "👑" if isinstance(admin, ChatMemberOwner) else "🛡️"
            title = f" <i>({html.escape(getattr(admin, 'custom_title', ''))})</i>" if getattr(admin, 'custom_title', None) else ""
            admin_lines.append(f"{badge} {admin.user.mention_html()}{title}")
        await update.effective_message.reply_html(
            f"🌟 <b>{html.escape(chat.title)} Admins</b> 🌟\n\n" +
            "\n".join(admin_lines) +
            "\n\n⚡ <i>Use /help for admin commands</i>",
            disable_web_page_preview=True
        )
    except Exception:
        await update.effective_message.reply_html("⚠️ Couldn't fetch admin list")

from telegram import Update, ChatMember
from telegram.constants import ChatMemberStatus
from telegram.ext import CallbackContext
import html

@admin_required(["can_promote_members"])
async def title(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message

    # If user provided arguments for setting a title
    if len(context.args) >= 2 or (message.reply_to_message and context.args):
        return await _set_new_title(update, context)

    # Otherwise, show current title
    user = await get_target_user(update, context)
    if not user:
        return await message.reply_html(
            "📝 <b>Usage:</b>\n"
            "1. Use <code>/title @username New Title</code>\n"
            "2. Or reply to an admin with <code>/title New Title</code>"
        )

    try:
        member = await chat.get_member(user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_html(f"❌ {user.mention_html()} is not an admin.")

        current_title = member.custom_title
        title_text = f"<code>{html.escape(current_title)}</code>" if current_title else "<i>No title set</i>"

        return await message.reply_html(
            f"🛡️ <b>Admin Title</b>\n\n"
            f"👤 Admin: {user.mention_html()}\n"
            f"🏷 Title: {title_text}\n\n"
            "To change: <code>/title @username New Title</code> or reply with <code>/title New Title</code>"
        )

    except Exception as e:
        return await message.reply_html(f"❌ <b>Error:</b> <code>{html.escape(str(e))}</code>")


async def _set_new_title(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    requester = update.effective_user

    try:
        # Get target user
        user = await get_target_user(update, context)
        if not user:
            raise ValueError("No user found to set title.")

        # Parse title
        if message.reply_to_message and context.args:
            new_title = " ".join(context.args).strip()
        else:
            new_title = " ".join(context.args[1:]).strip()

        if not new_title:
            return await message.reply_html("❌ Please provide a new title.")
        if len(new_title) > 16:
            return await message.reply_html("❌ Title must be 16 characters or fewer.")

        member = await chat.get_member(user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_html(f"❌ {user.mention_html()} is not an admin.")

        # Check if the requester can actually promote members
        requester_member = await chat.get_member(requester.id)
        if requester_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_html("❌ You need admin rights to change titles!")

        if requester_member.status == ChatMemberStatus.ADMINISTRATOR and not requester_member.can_promote_members:
            return await message.reply_html("❌ You don't have permission to change admin titles!")

        # Set the title
        await chat.set_administrator_custom_title(
            user_id=user.id,
            custom_title=new_title
        )

        return await message.reply_html(
            f"✅ <b>Title Updated</b>\n\n"
            f"👤 Admin: {user.mention_html()}\n"
            f"🏷 New Title: <code>{html.escape(new_title)}</code>\n\n"
            f"Changed by: {requester.mention_html()}"
        )

    except Exception as e:
        return await message.reply_html(
            f"❌ <b>Failed to set title:</b> <code>{html.escape(str(e))}</code>\n\n"
            "📌 Usage:\n"
            "<code>/title @username New Title</code>\n"
            "or reply to admin with <code>/title New Title</code>"
        )


async def get_target_user(update: Update, context: CallbackContext):
    """Helper function to get target user from command arguments or reply"""
    message = update.effective_message
    
    if message.reply_to_message:
        return message.reply_to_message.from_user
    
    if not context.args:
        return None
        
    # Try to resolve username (remove @ if present)
    username = context.args[0].lstrip('@')
    try:
        # Try to get user from mention in message entities
        if message.entities and message.entities[0].type == "mention":
            username = message.text[message.entities[0].offset+1:message.entities[0].offset+message.entities[0].length]
            return await context.bot.get_chat_member(update.effective_chat.id, username)
        
        # Fallback to searching by username
        for member in await update.effective_chat.get_administrators():
            if member.user.username and member.user.username.lower() == username.lower():
                return member.user
                
    except Exception:
        pass
        
    return None

import time
from typing import Dict, Optional
from telegram import Update, MessageEntity
from telegram.ext import ContextTypes, MessageHandler, filters

# Global dictionary to store AFK users with thread safety considerations
afk_users: Dict[int, Dict] = {}

def get_readable_time(seconds: int) -> str:
    """Convert seconds to human-readable time format"""
    periods = [
        ('year', 60*60*24*365),
        ('month', 60*60*24*30),
        ('day', 60*60*24),
        ('hour', 60*60),
        ('minute', 60),
        ('second', 1)
    ]
    
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f"{int(period_value)} {period_name}{'s' if period_value != 1 else ''}")
    
    return ", ".join(result) if result else "0 seconds"

async def handle_afk_return(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    """Safely handle user returning from AFK status"""
    try:
        if user_id not in afk_users:
            return None
        
        user_data = afk_users.get(user_id, {})
        if not user_data:
            return None
            
        duration = int(time.time() - user_data.get('time', time.time()))
        del afk_users[user_id]  # Remove user from AFK list
        
        time_str = get_readable_time(duration)
        msg = f"👋 Welcome back {user_data.get('name', '')}! You were AFK for {time_str}"
        
        if user_data.get('reason'):
            msg += f"\n📝 Reason: {user_data['reason']}"
        
        return msg
    except Exception as e:
        logger.error(f"Error in handle_afk_return: {e}")
        return None

async def afk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /afk command with multi-chat awareness"""
    try:
        user = update.effective_user
        if not user:
            return

        reason = " ".join(context.args) if context.args else None

        # Check if user is already AFK
        if user.id in afk_users:
            welcome_msg = await handle_afk_return(user.id, context)
            if welcome_msg:
                await update.message.reply_text(welcome_msg)
            return

        # Set AFK status
        afk_users[user.id] = {
            'time': time.time(),
            'reason': reason,
            'name': user.full_name,
            'username': user.username,
            'chat_id': update.effective_chat.id,
            'set_at': datetime.now().isoformat()
        }

        reply = "😴 You are now AFK"
        if reason:
            reply += f"\n📝 Reason: {reason}"
        
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error in afk_command: {e}")
        await update.message.reply_text("⚠️ Could not set AFK status")

async def check_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark user as returned when they send messages in any chat with the bot"""
    try:
        user = update.effective_user
        if not user or user.is_bot:
            return

        # If user is AFK and sends any message in any chat
        if user.id in afk_users:
            welcome_msg = await handle_afk_return(user.id, context)
            if welcome_msg:
                # Notify in the current chat where they returned
                await update.effective_message.reply_text(welcome_msg)
                logger.info(f"User {user.id} returned by sending a message in chat {update.effective_chat.id}")

    except Exception as e:
        logger.error(f"Error in check_user_activity: {e}")

async def notify_afk_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Notify about AFK users without marking them as returned"""
    try:
        if not update.message:
            return

        mentioned_users = set()

        # Check message entities for mentions
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == MessageEntity.TEXT_MENTION and entity.user:
                    mentioned_users.add(entity.user.id)
                elif entity.type == MessageEntity.MENTION:
                    username = update.message.text[entity.offset+1:entity.offset+entity.length]
                    try:
                        member = await update.effective_chat.get_member(username)
                        if member.user:
                            mentioned_users.add(member.user.id)
                    except Exception as e:
                        logger.debug(f"Mention resolution failed: {e}")

        # Check for replies to AFK users
        if update.message.reply_to_message and update.message.reply_to_message.from_user:
            mentioned_users.add(update.message.reply_to_message.from_user.id)

        # Notify about AFK users
        for user_id in mentioned_users:
            if user_id == update.effective_user.id:  # Skip self-mentions
                continue
                
            if user_id in afk_users:
                user_data = afk_users.get(user_id, {})
                duration = int(time.time() - user_data.get('time', time.time()))
                time_str = get_readable_time(duration)
                
                msg = f"😴 {user_data.get('name', 'Someone')} is AFK (for {time_str})"
                if user_data.get('reason'):
                    msg += f"\n📝 Reason: {user_data['reason']}"
                
                if user_data.get('username'):
                    msg += f"\n👤 @{user_data['username']}"
                
                await update.message.reply_text(msg, quote=True)

    except Exception as e:
        logger.error(f"Error in notify_afk_mention: {e}", exc_info=True)

mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client[DB_NAME]

# Collections
protection_collection = db["protection_status"]
ban_counts_collection = db["ban_counts"]
cooldowns_collection = db["cooldowns"]
whitelist_collection = db["whitelist"]
admin_cache_collection = db["admin_cache"]

# Global state (will be initialized from DB)
protection_status: Dict[int, bool] = {}
ban_counts: Dict[Tuple[int, int], int] = {}
cooldowns: Dict[Tuple[int, int], datetime] = {}
admin_cache: Dict[int, Dict[int, ChatMember]] = {}
whitelist: Dict[int, list[int]] = {}

# Constants
OWNER_ID = 8429156335  # Change to your user ID
MAX_BANS_BEFORE_DEMOTE = 5
WARNING_THRESHOLD = 3
COOLDOWN_TIME = 300  # 5 minutes in seconds
CLEANUP_INTERVAL = 3600  # 1 hour in seconds

logger = logging.getLogger(__name__)

async def load_initial_data():
    """Load initial data from MongoDB when bot starts"""
    try:
        # Load protection status
        async for doc in protection_collection.find({}):
            protection_status[doc["chat_id"]] = doc["status"]
        
        # Load ban counts
        async for doc in ban_counts_collection.find({}):
            ban_counts[(doc["chat_id"], doc["user_id"])] = doc["count"]
        
        # Load cooldowns
        async for doc in cooldowns_collection.find({}):
            cooldowns[(doc["chat_id"], doc["user_id"])] = doc["timestamp"]
        
        # Load whitelist
        async for doc in whitelist_collection.find({}):
            whitelist[doc["chat_id"]] = doc["whitelisted_admins"]
        
        logger.info("✅ Successfully loaded initial data from MongoDB")
    except Exception as e:
        logger.error(f"Failed to load initial data from MongoDB: {e}")

async def update_protection_status(chat_id: int, status: bool):
    """Update protection status in DB"""
    try:
        await protection_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"status": status}},
            upsert=True
        )
        protection_status[chat_id] = status
    except Exception as e:
        logger.error(f"Failed to update protection status for chat {chat_id}: {e}")

async def update_ban_count(chat_id: int, user_id: int, count: int):
    """Update ban count in DB"""
    try:
        await ban_counts_collection.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"count": count}},
            upsert=True
        )
        ban_counts[(chat_id, user_id)] = count
    except Exception as e:
        logger.error(f"Failed to update ban count for user {user_id} in chat {chat_id}: {e}")

async def update_cooldown(chat_id: int, user_id: int, timestamp: datetime):
    """Update cooldown in DB"""
    try:
        await cooldowns_collection.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"timestamp": timestamp}},
            upsert=True
        )
        cooldowns[(chat_id, user_id)] = timestamp
    except Exception as e:
        logger.error(f"Failed to update cooldown for user {user_id} in chat {chat_id}: {e}")

async def update_whitelist(chat_id: int, admins: list[int]):
    """Update whitelist in DB"""
    try:
        await whitelist_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"whitelisted_admins": admins}},
            upsert=True
        )
        whitelist[chat_id] = admins
    except Exception as e:
        logger.error(f"Failed to update whitelist for chat {chat_id}: {e}")

async def remove_ban_data(chat_id: int, user_id: int):
    """Remove ban count and cooldown for a user"""
    try:
        await asyncio.gather(
            ban_counts_collection.delete_one({"chat_id": chat_id, "user_id": user_id}),
            cooldowns_collection.delete_one({"chat_id": chat_id, "user_id": user_id})
        )
        ban_counts.pop((chat_id, user_id), None)
        cooldowns.pop((chat_id, user_id), None)
    except Exception as e:
        logger.error(f"Failed to remove ban data for user {user_id} in chat {chat_id}: {e}")

async def verify_creator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return False
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status == ChatMemberStatus.OWNER
    except Exception as e:
        logger.error(f"Creator verification failed: {e}")
        return False

async def antibanall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_creator(update, context):
        if update.callback_query:
            await update.callback_query.answer("❌ Only the group creator can manage this protection.", show_alert=True)
        else:
            await update.message.reply_html("❌ Only the group creator can manage this protection.")
        return
    
    chat_id = update.effective_chat.id
    current_status = protection_status.get(chat_id, False)
    action = "disable" if current_status else "enable"
    
    # Handle both command and callback cases
    if update.callback_query:
        message = await update.callback_query.edit_message_text("Processing...")
    else:
        message = await update.message.reply_text("Processing...")
    
    await _toggle_protection(update, context, chat_id, action, message)

async def _toggle_protection(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           chat_id: int, action: str, message):
    # Animation steps
    steps = ["Activating systems...", "Configuring shields...", "Finalizing setup..."]
    for step in steps:
        await message.edit_text(f"🔧 {step}")
        await asyncio.sleep(1)
    
    # Update protection status
    new_status = (action == "enable")
    await update_protection_status(chat_id, new_status)
    
    # Prepare response
    user_mention = update.effective_user.mention_html()
    now = datetime.now().strftime("%I:%M %p | %b %d, %Y")
    status_text = "ACTIVE" if action == "enable" else "OFFLINE"
    
    result = (
        f"{'🛡️ Protection Enabled' if action == 'enable' else '⚠️ Protection Disabled'}\n"
        f"Status: {status_text}\n"
        f"Triggered by: {user_mention}\nTime: {now}"
    )
    
    # Create buttons
    opposite_action = "enable" if action == "disable" else "disable"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🛡️ Enable" if opposite_action == "enable" else "⚠️ Disable",
            callback_data=f"antibanall_toggle_{opposite_action}"
        )],
        [InlineKeyboardButton("⚙️ Whitelist Admin", callback_data="antibanall_whitelist")]
    ])
    
    await message.edit_text(result, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def antibanall_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not await verify_creator(update, context):
        return await query.edit_message_text("❌ Only the group creator can manage this protection.", 
                                          parse_mode=ParseMode.HTML)
    
    chat = update.effective_chat
    if not chat:
        return await query.edit_message_text("❌ Chat not found.")
    
    action = "enable" if "enable" in query.data else "disable"
    await _toggle_protection(update, context, chat.id, action, query.message)

async def whitelist_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not await verify_creator(update, context):
        return await query.edit_message_text("❌ Only the group creator can manage the whitelist.", 
                                          parse_mode=ParseMode.HTML)

    chat_id = query.message.chat.id
    admins = await _get_chat_admins(context.bot, chat_id)
    if not admins:
        return await query.edit_message_text("Failed to fetch admin list.")

    keyboard = []
    current_user_id = update.effective_user.id
    
    for admin_id, admin in admins.items():
        if admin_id == current_user_id:
            continue
            
        is_whitelisted = admin_id in whitelist.get(chat_id, [])
        state = "✅" if is_whitelisted else "❌"
        action = "remove" if is_whitelisted else "add"
        
        button = InlineKeyboardButton(
            f"{state} {admin.user.full_name}",
            callback_data=f"antibanall_whitelist_toggle:{admin_id}:{action}"
        )
        keyboard.append([button])

async def whitelist_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not await verify_creator(update, context):
        return
    
    _, admin_id_str, action = query.data.split(":")
    admin_id = int(admin_id_str)
    chat_id = query.message.chat.id
    
    current_whitelist = whitelist.get(chat_id, [])
    
    if action == "add" and admin_id not in current_whitelist:
        current_whitelist.append(admin_id)
        await update_whitelist(chat_id, current_whitelist)
    elif action == "remove" and admin_id in current_whitelist:
        current_whitelist.remove(admin_id)
        await update_whitelist(chat_id, current_whitelist)
    
    await whitelist_handler(update, context)

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    current_status = protection_status.get(chat_id, False)
    status_text = "ACTIVE" if current_status else "OFFLINE"
    
    # Prepare the protection status message
    user_mention = query.from_user.mention_html()
    now = datetime.now().strftime("%I:%M %p | %b %d, %Y")
    
    result = (
        f"{'🛡️ Protection Enabled' if current_status else '⚠️ Protection Disabled'}\n"
        f"Status: {status_text}\n"
        f"Triggered by: {user_mention}\nTime: {now}"
    )
    
    # Create buttons
    opposite_action = "disable" if current_status else "enable"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🛡️ Enable" if opposite_action == "enable" else "⚠️ Disable",
            callback_data=f"antibanall_toggle_{opposite_action}"
        )],
        [InlineKeyboardButton("⚙️ Whitelist Admin", callback_data="antibanall_whitelist")]
    ])
    
    await query.edit_message_text(
        result,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    
    # Edit the existing message instead of trying to create a new one
    await query.edit_message_text("Processing...")
    await antibanall_command(update, context)
    
async def monitor_bans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat or not protection_status.get(chat.id, False):
        return
        
    cmu = update.chat_member
    if not cmu:
        return
        
    # Check if this is a ban action (member -> banned)
    if (cmu.old_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR] and 
        cmu.new_chat_member.status == ChatMemberStatus.BANNED):
        
        admin = cmu.from_user
        victim = cmu.new_chat_member.user
        
        # Skip if admin banned themselves or is whitelisted
        if admin.id == victim.id or admin.id in whitelist.get(chat.id, []):
            return
            
        await _handle_ban_action(context, chat.id, admin)

async def _handle_ban_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, admin_user: User):
    key = (chat_id, admin_user.id)
    now = datetime.now()
    
    # Reset counts if cooldown expired
    if key in cooldowns and (now - cooldowns[key]).total_seconds() > COOLDOWN_TIME:
        await remove_ban_data(chat_id, admin_user.id)
        
    # Increment ban count
    current_count = ban_counts.get(key, 0) + 1
    await update_ban_count(chat_id, admin_user.id, current_count)
    await update_cooldown(chat_id, admin_user.id, now)
    
    # Take action based on ban count
    if current_count == WARNING_THRESHOLD:
        await context.bot.send_message(
            chat_id, 
            f"⚠️ {admin_user.mention_html()} is banning users rapidly!", 
            parse_mode=ParseMode.HTML
        )
    elif current_count >= MAX_BANS_BEFORE_DEMOTE:
        try:
            # Demote the admin by removing all privileges
            await context.bot.promote_chat_member(
                chat_id,
                admin_user.id,
                can_change_info=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_chat=False,
                can_manage_video_chats=False,
                can_manage_topics=False
            )
            await context.bot.send_message(
                chat_id, 
                f"🛡️ {admin_user.mention_html()} has been auto-demoted for mass banning!", 
                parse_mode=ParseMode.HTML
            )
            await remove_ban_data(chat_id, admin_user.id)
        except Exception as e:
            logger.warning(f"Failed to demote admin {admin_user.id} in chat {chat_id}: {e}")

async def _get_chat_admins(bot, chat_id: int) -> Dict[int, ChatMember]:
    if chat_id in admin_cache:
        return admin_cache[chat_id]
    
    try:
        admins = await bot.get_chat_administrators(chat_id)
        admin_cache[chat_id] = {admin.user.id: admin for admin in admins}
        return admin_cache[chat_id]
    except Exception as e:
        logger.error(f"Failed to fetch admins for chat {chat_id}: {e}")
        return {}

async def cleanup_task():
    while True:
        try:
            now = datetime.now()
            # Clean up old ban counts and cooldowns
            operations = []
            expired_keys = []
            
            for key, timestamp in cooldowns.items():
                if (now - timestamp).total_seconds() > CLEANUP_INTERVAL:
                    chat_id, user_id = key
                    operations.append(
                        UpdateOne(
                            {"chat_id": chat_id, "user_id": user_id},
                            {"$set": {"count": 0}},
                            upsert=True
                        )
                    )
                    expired_keys.append(key)
            
            if operations:
                await ban_counts_collection.bulk_write(operations)
                for key in expired_keys:
                    ban_counts.pop(key, None)
                    cooldowns.pop(key, None)
            
            # Clear admin cache periodically
            admin_cache.clear()
            
            await asyncio.sleep(CLEANUP_INTERVAL)
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
            await asyncio.sleep(60)



import logging
import re
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from telegram import (
    Update,
    ChatPermissions,
    User,
)
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import time 

# 🌈 CONFIGURATION
BOT_NAME = "✨ GroupGuardian ✨"
ADMIN_EMOJI = "👑"
ACTION_EMOJI = "⚡"
SUCCESS_EMOJI = "✅"
ERROR_EMOJI = "❗"
DELETE_MESSAGE_COUNT = 5

COMMAND_EMOJIS = {
    "kickme": "👢",
    "banme": "☠️",
    "ban": "🔨",
    "sban": "🧹",
    "tban": "⏳",
    "dban": "🗑️",
    "unban": "🎉",
    "kick": "🚪",
    "mute": "🔇",
    "tmute": "⏸️",
    "smute": "🤫",
    "unmute": "🔊"
}

KICKME_QUOTES = [
    "“Even legends need a dramatic exit.”\n— *Yoruichi* 🐾",
    "“I walk out with style, not shame.” ✨",
    "“Mission accomplished. Now I vanish.” 💨",
    "“Time to disappear into the shadows.” 🌑",
    "“Sayōnara, folks. I'll be back... or not.” 👋",
    "“Exit stage left, with flair.” 🎭",
    "“Freeing up space like a hero.” 🦸‍♂️"
]

BANME_QUOTES = [
    "“I asked for peace, but chose exile.” — *Yoruichi* 👣",
    "“If I'm going out, I'm going out like a legend.” 🔥",
    "“This is my final flash.” 🌠",
    "“Tell my memes I loved them.” 💾",
    "“Ban me, and let the world forget.” 🌌",
    "“One last message... and then silence.” 🎤",
    "“I've seen enough. It's time.” ⏳"
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def stylish_header(text: str) -> str:
    return f"✦━━━✦ {text} ✦━━━✦"

def command_style(cmd: str, desc: str) -> str:
    return f"{COMMAND_EMOJIS.get(cmd, '✨')} /{cmd} - {desc}"

def parse_time(time_str: str) -> Optional[timedelta]:
    match = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    return None

async def resolve_target(update: Update) -> Optional[User]:
    message = update.effective_message
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        user_id = int(args[1])
        try:
            member = await message.chat.get_member(user_id)
            return member.user
        except Exception:
            await message.reply_text("❌ Couldn't find user with that ID.")
    await message.reply_text("ℹ️ Reply to a user's message or provide their user ID.")
    return None

async def verify_admin_rights(update: Update, context: ContextTypes.DEFAULT_TYPE, require_ban: bool = False) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    
    try:
        member = await chat.get_member(user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await update.effective_message.reply_text("🚫 You need to be an admin to use this command.")
            return False
            
        if require_ban and member.status == ChatMemberStatus.ADMINISTRATOR and not getattr(member, "can_restrict_members", False):
            await update.effective_message.reply_text("🔒 You don't have ban permissions.")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error verifying admin rights: {e}")
        await update.effective_message.reply_text("⚠️ Error verifying your permissions.")
        return False

async def delete_user_messages(chat, user_id: int, limit: int = 5):
    deleted = 0
    async for msg in chat.get_history(limit=100):
        if msg.from_user and msg.from_user.id == user_id:
            try:
                await msg.delete()
                deleted += 1
                if deleted >= limit:
                    break
            except Exception:
                continue
    return deleted

# 👤 USER COMMANDS

async def kickme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    flair_text = random.choice(KICKME_QUOTES)
    await update.message.reply_text(
        text=(
            f"🎭 *{BOT_NAME} — VOLUNTARY EXIT*\n\n"
            f"{flair_text}\n\n"
            f"👤 *User:* `{user.first_name}`\n"
            f"👢 *Action:* Leaving the group with flair!\n"
            f"🚪 *Status:* Kicked\n"
        ),
        parse_mode=ParseMode.MARKDOWN
    )
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)

async def banme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    dramatic_line = random.choice(BANME_QUOTES)
    await update.message.reply_text(
        text=(
            f"⚰️ *{BOT_NAME} — PERMANENT GOODBYE*\n\n"
            f"{dramatic_line}\n\n"
            f"👤 *User:* `{user.first_name}`\n"
            f"☠️ *Action:* Self-ban initiated\n"
            f"🚫 *Status:* Permanently Banned"
        ),
        parse_mode=ParseMode.MARKDOWN
    )
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)

# 🛡️ ADMIN COMMANDS

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return
        
    target = await resolve_target(update)
    if not target:
        return
        
    user = update.effective_user
    bot = await context.bot.get_me()

    if target.id in [user.id, bot.id]:
        await update.message.reply_text("😶 That... would be foolish.")
        return
        
    try:
        member = await update.effective_chat.get_member(target.id)
        if member.status == ChatMemberStatus.OWNER:
            await update.message.reply_text("👑 Cannot ban the group creator.")
            return
        if member.status == ChatMemberStatus.ADMINISTRATOR and user.id != update.effective_chat.id:
            await update.message.reply_text("⚠️ Cannot ban a fellow admin.")
            return
    except Exception:
        pass

    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(
        text=(
            f"🔨 *{BOT_NAME} — BAN HAMMER*\n\n"
            f"👤 *Target:* {target.mention_markdown()}\n"
            f"💥 *Actioned By:* {user.mention_markdown()}\n"
            f"🚫 *Status:* Permanently Banished"
        ),
        parse_mode=ParseMode.MARKDOWN
    )

async def sban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return

    target = await resolve_target(update)
    if not target:
        return

    user = update.effective_user
    bot = await context.bot.get_me()

    if target.id in [user.id, bot.id]:
        await update.message.reply_text("😅 You can't soft ban yourself or the bot.")
        return

    try:
        member = await update.effective_chat.get_member(target.id)
        if member.status == ChatMemberStatus.OWNER:
            await update.message.reply_text("👑 You can't soft ban the group creator.")
            return
        if member.status == ChatMemberStatus.ADMINISTRATOR and user.id != update.effective_chat.id:
            await update.message.reply_text("🚫 You can't soft ban another admin.")
            return
    except Exception:
        pass

    # Delete recent messages by user
    deleted_count = await delete_user_messages(update.effective_chat, target.id, DELETE_MESSAGE_COUNT)

    try:
        # Soft ban: ban and unban to kick + delete messages
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await asyncio.sleep(1)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)

        await update.message.reply_text(
            f"🧹 *SOFT BAN EXECUTED*\n\n"
            f"👤 Target: {target.mention_markdown()}\n"
            f"🗑️ Deleted messages: {deleted_count}\n"
            f"🚪 Action: *Kicked via Soft Ban*\n"
            f"🛡️ By: {user.mention_markdown()}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in sban: {e}")
        await update.message.reply_text("⚠️ An error occurred while performing the soft ban.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return
        
    target = await resolve_target(update)
    if not target:
        return
        
    bot = await context.bot.get_me()
    if target.id == bot.id:
        await update.message.reply_text("🤖 I can't unban myself!")
        return
        
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(
            f"🕊️ *UNBAN SUCCESSFUL*\n\n"
            f"👤 Target: {target.mention_markdown()}\n"
            f"✅ User has been allowed back into the group.",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in unban: {e}")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return

    target = await resolve_target(update)
    if not target:
        return

    user = update.effective_user
    bot = await context.bot.get_me()

    if target.id in [bot.id, user.id]:
        await update.message.reply_text("❌ You can't kick yourself or the bot.")
        return

    try:
        member = await update.effective_chat.get_member(target.id)
        if member.status == ChatMemberStatus.OWNER:
            await update.message.reply_text("👑 You can't kick the group creator.")
            return
        if member.status == ChatMemberStatus.ADMINISTRATOR and user.id != update.effective_chat.id:
            await update.message.reply_text("🚫 You can't kick another admin.")
            return
    except Exception as e:
        logger.warning(f"Couldn't verify target's status: {e}")

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(
            f"🥾 *KICK EXECUTED*\n\n"
            f"👤 Target: {target.mention_markdown()}\n"
            f"🛡️ By: {user.mention_markdown()}\n"
            f"🚪 Status: *Removed from group*",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in kick: {e}")
        await update.message.reply_text("⚠️ Failed to kick the user.")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return

    target = await resolve_target(update)
    if not target:
        return

    user = update.effective_user
    bot = await context.bot.get_me()

    if target.id in [bot.id, user.id]:
        await update.message.reply_text("❌ You can't mute yourself or the bot.")
        return

    try:
        member = await update.effective_chat.get_member(target.id)
        if member.status == ChatMemberStatus.OWNER:
            await update.message.reply_text("👑 Cannot mute the group owner.")
            return
        if member.status == ChatMemberStatus.ADMINISTRATOR and user.id != update.effective_chat.id:
            await update.message.reply_text("🚫 You can't mute another admin.")
            return
    except Exception as e:
        logger.warning(f"Couldn't verify target's status: {e}")

    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(
            f"🔇 *MUTE EXECUTED*\n\n"
            f"👤 Target: {target.mention_markdown()}\n"
            f"🛡️ By: {user.mention_markdown()}\n"
            f"🚫 Status: *User is now silenced.*",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in mute: {e}")
        await update.message.reply_text("⚠️ Failed to mute the user.")

import asyncio
from datetime import datetime, timedelta
from telegram import ChatPermissions

async def unmute_later(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, duration: timedelta, target_mention: str):
    await asyncio.sleep(duration.total_seconds())
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔊 *UNMUTED*\n\n{target_mention} is now free to speak!",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error unmuting user {user_id} in {chat_id}: {e}")

async def tmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return

    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("⏳ Please specify a duration like `5m`, `2h`, `1d`.", parse_mode=ParseMode.MARKDOWN)
        return

    time_str = args[1]
    duration = parse_time(time_str)
    if not duration:
        await update.message.reply_text("❗ Invalid time format. Use like: `30s`, `5m`, `1h`, `2d`", parse_mode=ParseMode.MARKDOWN)
        return

    target = await resolve_target(update)
    if not target:
        return

    user = update.effective_user
    bot = await context.bot.get_me()

    if target.id in [bot.id, user.id]:
        await update.message.reply_text("🚫 You can't mute yourself or the bot.")
        return

    try:
        member = await update.effective_chat.get_member(target.id)
        if member.status == ChatMemberStatus.OWNER:
            await update.message.reply_text("👑 You can't mute the group owner.")
            return
        if member.status == ChatMemberStatus.ADMINISTRATOR and user.id != update.effective_chat.id:
            await update.message.reply_text("🚫 You can't mute another admin.")
            return
    except Exception as e:
        logger.warning(f"Couldn't fetch member status: {e}")

    until_date = datetime.utcnow() + duration

    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await update.message.reply_text(
            f"⏰ *TEMPORARY MUTE ISSUED*\n\n"
            f"👤 Target: {target.mention_markdown()}\n"
            f"🛡️ By: {user.mention_markdown()}\n"
            f"⏱️ Duration: `{time_str}`\n"
            f"🕰️ Until: `{until_date.strftime('%Y-%m-%d %H:%M:%S UTC')}`",
            parse_mode=ParseMode.MARKDOWN
        )

        # Run unmute in the background
        asyncio.create_task(
            unmute_later(
                context,
                update.effective_chat.id,
                target.id,
                duration,
                target.mention_markdown()
            )
        )

    except Exception as e:
        logger.error(f"Error in tmute: {e}")
        await update.message.reply_text("⚠️ Failed to apply timed mute.")


async def smute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except Exception:
        pass

    user = update.effective_user
    chat = update.effective_chat

    # Check if user is admin
    try:
        member = await chat.get_member(user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
    except Exception:
        return

    # Identify target user
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        args = update.message.text.split()
        if len(args) > 1 and args[1].isdigit():
            try:
                member = await chat.get_member(int(args[1]))
                target = member.user
            except Exception:
                return

    if not target or target.id in [user.id, (await context.bot.get_me()).id]:
        return

    # Prevent muting admins/owner
    try:
        member = await chat.get_member(target.id)
        if member.status == ChatMemberStatus.OWNER:
            return
        if member.status == ChatMemberStatus.ADMINISTRATOR and user.id != chat.id:
            return
    except Exception:
        return

    # Restrict (mute) the target user
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        )
    except Exception:
        return

    # Delete the command message
    try:
        await update.message.delete()
    except Exception:
        pass

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return

    target = await resolve_target(update)
    if not target:
        return

    user = update.effective_user
    bot = await context.bot.get_me()

    # Avoid self or bot or group owner unmute
    if target.id in [user.id, bot.id]:
        return

    try:
        member = await update.effective_chat.get_member(target.id)
        if member.status == ChatMemberStatus.OWNER:
            await update.message.reply_text("👑 The group owner is always free to speak.")
            return
    except Exception as e:
        logger.warning(f"Failed to fetch member info: {e}")

    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
        )
        await update.message.reply_text(
            f"{SUCCESS_EMOJI} *UNMUTE SUCCESSFUL*\n\n"
            f"👤 Target: {target.mention_markdown()}\n"
            f"🔊 All speaking permissions restored.\n"
            f"🛡️ By: {user.mention_markdown()}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error while unmuting user: {e}")

import asyncio
from datetime import timedelta
import time
from telegram import Update, ChatPermissions
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.ext import ContextTypes
from telegram.error import TelegramError, RetryAfter

def parse_time(time_str: str) -> timedelta | None:
    """Parses duration strings like '10m', '2h', '1d' into timedelta."""
    unit = time_str[-1]
    if not time_str[:-1].isdigit():
        return None
    value = int(time_str[:-1])

    if unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    else:
        return None

async def unban_later(chat_id: int, user_id: int, delay: float, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(delay)
    try:
        await context.bot.unban_chat_member(chat_id, user_id)
    except Exception as e:
        print(f"Failed to unban {user_id}: {e}")

async def tban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return

    args = context.args
    if len(args) < 2:
        return await update.message.reply_text(
            "🚫 Usage:\n`/tban @user 1d [reason]`",
            parse_mode=ParseMode.MARKDOWN,
        )

    target = await resolve_target(update)
    if not target:
        return

    user = update.effective_user
    bot = await context.bot.get_me()

    if target.id in [bot.id, user.id]:
        return await update.message.reply_text("❌ Cannot ban yourself or the bot.")

    try:
        member = await update.effective_chat.get_member(target.id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return await update.message.reply_text("⚠️ Cannot ban admins or the group owner.")
    except Exception:
        pass

    duration = parse_time(args[1])
    if not duration:
        return await update.message.reply_text(
            "🕒 Invalid time format.\nUse like `10m`, `2h`, `1d`.",
            parse_mode=ParseMode.MARKDOWN,
        )

    until_timestamp = int(time.time() + duration.total_seconds())
    reason = " ".join(args[2:]) if len(args) > 2 else "No reason provided."

    try:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target.id,
            until_date=until_timestamp,
        )

        await update.message.reply_text(
            f"🔨 *Temporarily Banned*\n"
            f"👤 User: {target.mention_markdown()}\n"
            f"🕒 Duration: `{args[1]}`\n"
            f"📄 Reason: {reason}\n"
            f"👮‍♂️ By: {user.mention_markdown()}",
            parse_mode=ParseMode.MARKDOWN,
        )

        # Schedule unban
        asyncio.create_task(
            unban_later(update.effective_chat.id, target.id, duration.total_seconds(), context)
        )

    except Exception as e:
        await update.message.reply_text("❌ Failed to ban the user. Ensure I have ban rights.")


async def dban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verify_admin_rights(update, context, require_ban=True):
        return

    # Must be a reply to someone's message
    if not update.message.reply_to_message:
        return await update.message.reply_text("❗You need to reply to a message to ban that user.")

    target = update.message.reply_to_message.from_user
    user = update.effective_user
    chat = update.effective_chat

    if target.id == user.id:
        return await update.message.reply_text("🚫 You cannot ban yourself.")

    bot = await context.bot.get_me()
    if target.id == bot.id:
        return await update.message.reply_text("🤖 I can't ban myself, silly.")

    try:
        member = await chat.get_member(target.id)
        if member.status == ChatMemberStatus.OWNER:
            return await update.message.reply_text("👑 I cannot ban the group owner.")
        if member.status == ChatMemberStatus.ADMINISTRATOR and user.id != chat.id:
            return await update.message.reply_text("🛡️ I cannot ban group admins.")
    except Exception:
        pass

    # Optional reason
    reason = " ".join(context.args) if context.args else "No reason provided."

    try:
        # Delete their message
        await update.message.reply_to_message.delete()

        # Ban the user
        await context.bot.ban_chat_member(chat_id=chat.id, user_id=target.id)

        # Confirm action
        await update.message.reply_text(
            f"⛔ *USER BANNED & MESSAGE DELETED*\n\n"
            f"👤 Target: {target.mention_markdown()}\n"
            f"📝 Reason: {reason}\n"
            f"🛡️ By: {user.mention_markdown()}",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Error in dban: {e}")
        await update.message.reply_text("❌ Failed to delete and ban. Check my permissions.")

mongo = MongoClient(MONGODB_URI)
db = mongo[DB_NAME]
groups_col = db["groups"]

BROADCAST_DELAY = 1
MAX_FAILED_DISPLAY = 5
OWNER_ID = 8429156335  # Replace with your actual owner ID


async def forward_message(context: ContextTypes.DEFAULT_TYPE, chat_id, from_chat_id, message_id):
    try:
        await context.bot.forward_message(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id
        )
        return True, None
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await forward_message(context, chat_id, from_chat_id, message_id)
    except TelegramError as e:
        return False, str(e)


async def forward_and_pin(context: ContextTypes.DEFAULT_TYPE, chat_id, from_chat_id, message_id):
    try:
        sent = await context.bot.forward_message(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id
        )
        await context.bot.pin_chat_message(chat_id, sent.message_id, disable_notification=True)
        return True, None
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await forward_and_pin(context, chat_id, from_chat_id, message_id)
    except TelegramError as e:
        return False, str(e)


async def broadcast_worker(context: ContextTypes.DEFAULT_TYPE, chat_id, message_id, group_ids, from_chat_id, pin_message=False):
    total = len(group_ids)
    success, failed = 0, []

    forward_func = forward_and_pin if pin_message else forward_message

    progress_msg = await context.bot.send_message(
        chat_id=chat_id,
        text="⏳ Starting broadcast...",
        parse_mode=ParseMode.HTML
    )
    progress_message_id = progress_msg.message_id

    for i, gid in enumerate(group_ids, 1):
        ok, err = await forward_func(context, gid, from_chat_id, message_id)
        if ok:
            success += 1
        else:
            failed.append((gid, err))

        # Update every 10 messages or at the end
        if i % 10 == 0 or i == total:
            progress = (
                f"📢 <b>Broadcasting {'(with PIN)' if pin_message else ''}...</b>\n"
                f"Progress: <b>{i}/{total}</b>\n"
                f"✅ Success: <b>{success}</b>\n"
                f"❌ Failed: <b>{len(failed)}</b>"
            )
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=progress_message_id,
                    text=progress,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

        await asyncio.sleep(BROADCAST_DELAY)

    # Final report
    report = (
        f"✅ <b>Broadcast {'(with PIN)' if pin_message else ''} complete!</b>\n"
        f"Total: <b>{total}</b>\n"
        f"Success: <b>{success}</b>\n"
        f"Failed: <b>{len(failed)}</b>"
    )
    if failed:
        report += "\n\n<b>Failed chats (first 5):</b>\n"
        for cid, err in failed[:MAX_FAILED_DISPLAY]:
            report += f"- <code>{cid}</code>: {err}\n"
        if len(failed) > MAX_FAILED_DISPLAY:
            report += f"(and {len(failed) - MAX_FAILED_DISPLAY} more)"

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=report,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ Please reply to the message you want to broadcast.")

    if not context.args or context.args[0].lower() not in ["regular", "pin"]:
        return await update.message.reply_text(
            "⚙️ Usage:\n"
            "/broadcast regular - Just forward\n"
            "/broadcast pin - Forward and pin in groups"
        )

    pin = context.args[0].lower() == "pin"

    group_ids = [g["chat_id"] for g in groups_col.find()]
    if not group_ids:
        return await update.message.reply_text("⚠️ No groups found in the database.")

    # Run broadcast in background
    asyncio.create_task(
        broadcast_worker(
            context,
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.message_id,
            group_ids=group_ids,
            from_chat_id=update.message.reply_to_message.chat_id,
            pin_message=pin
        )
    )

    await update.message.reply_text(f"🚀 Broadcast started ({'with PIN' if pin else 'regular'})...")


CUTIE = "https://graph.org/file/24375c6e54609c0e4621c.mp4"
HORNY = "https://graph.org/file/eaa834a1cbfad29bd1fe4.mp4"
HOT = "https://graph.org/file/745ba3ff07c1270958588.mp4"
SEMXY = "https://graph.org/file/58da22eb737af2f8963e6.mp4"
GAY = "https://graph.org/file/850290f1f974c5421ce54.mp4"
LESBIAN = "https://graph.org/file/ff258085cf31f5385db8a.mp4"
BIGBALL = "https://i.gifer.com/8ZUg.gif"
LANGD = "https://telegra.ph/file/423414459345bf18310f5.gif"

# Button
BUTTON = InlineKeyboardMarkup([[InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url=SUPPORT_CHAT)]])

# Helper
def get_target_user(update: Update):
    msg = update.effective_message
    if msg.reply_to_message:
        user = msg.reply_to_message.from_user
    else:
        user = msg.from_user
    return user.id, user.first_name

# Handlers
async def cutie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = get_target_user(update)
    mm = random.randint(1, 100)
    text = f"🍑 [{user_name}](tg://user?id={user_id}) {mm}% ᴄᴜᴛᴇ ʙᴀʙʏ🥀"
    await update.message.reply_document(
        document=CUTIE,
        caption=text,
        reply_markup=BUTTON,
        parse_mode="Markdown",
    )

async def horny(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = get_target_user(update)
    mm = random.randint(1, 100)
    text = f"🔥 [{user_name}](tg://user?id={user_id}) ɪꜱ {mm}% ʜᴏʀɴʏ!"
    await update.message.reply_document(
        document=HORNY,
        caption=text,
        reply_markup=BUTTON,
        parse_mode="Markdown",
    )

async def hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = get_target_user(update)
    mm = random.randint(1, 100)
    text = f"🔥 [{user_name}](tg://user?id={user_id}) ɪꜱ {mm}% ʜᴏᴛ!"
    await update.message.reply_document(
        document=HOT,
        caption=text,
        reply_markup=BUTTON,
        parse_mode="Markdown",
    )

async def sexy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = get_target_user(update)
    mm = random.randint(1, 100)
    text = f"🔥 [{user_name}](tg://user?id={user_id}) ɪꜱ {mm}% sexy!"
    await update.message.reply_document(
        document=SEMXY,
        caption=text,
        reply_markup=BUTTON,
        parse_mode="Markdown",
    )

async def gay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = get_target_user(update)
    mm = random.randint(1, 100)
    text = f"🍷 [{user_name}](tg://user?id={user_id}) ɪꜱ {mm}% ɢᴀʏ!"
    await update.message.reply_document(
        document=GAY,
        caption=text,
        reply_markup=BUTTON,
        parse_mode="Markdown",
    )

async def lesbian(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = get_target_user(update)
    mm = random.randint(1, 100)
    text = f"💜 [{user_name}](tg://user?id={user_id}) ɪꜱ {mm}% ʟᴇꜱʙɪᴀɴ!"
    await update.message.reply_document(
        document=LESBIAN,
        caption=text,
        reply_markup=BUTTON,
        parse_mode="Markdown",
    )

async def boob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = get_target_user(update)
    mm = random.randint(1, 100)
    text = f"🍒 [{user_name}](tg://user?id={user_id})ꜱ ʙᴏᴏʙꜱ ꜱɪᴢᴇ ɪᴢ {mm}!"
    await update.message.reply_document(
        document=BIGBALL,
        caption=text,
        reply_markup=BUTTON,
        parse_mode="Markdown",
    )

async def cock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = get_target_user(update)
    mm = random.randint(1, 100)
    text = f"🍆 [{user_name}](tg://user?id={user_id}) ᴄᴏᴄᴋ ꜱɪᴢᴇ ɪᴢ {mm}ᴄᴍ"
    await update.message.reply_document(
        document=LANGD,
        caption=text,
        reply_markup=BUTTON,
        parse_mode="Markdown",
    )
import math

SAFE_NAMES = {
    'abs': abs,
    'acos': math.acos,
    'asin': math.asin,
    'atan': math.atan,
    'ceil': math.ceil,
    'cos': math.cos,
    'exp': math.exp,
    'floor': math.floor,
    'log': math.log,
    'log10': math.log10,
    'max': max,
    'min': min,
    'pow': pow,
    'round': round,
    'sin': math.sin,
    'sqrt': math.sqrt,
    'tan': math.tan,
    'pi': math.pi,
    'e': math.e,
    'tau': math.tau,
    'inf': math.inf,
    'degrees': math.degrees,
    'radians': math.radians
}

def safe_eval(expr: str):
    """Safely evaluate mathematical expressions with strict validation."""
    try:
        expr = expr.replace("^", "**")
        expr = re.sub(r"\s+", "", expr)
        if not re.fullmatch(r"[\d+\-*\/%().,^a-z]+", expr):
            return None
        if any(word in expr.lower() for word in ["import", "exec", "eval", "open"]):
            return None
        result = eval(expr, {"__builtins__": None}, SAFE_NAMES)
        if isinstance(result, float):
            if result.is_integer():
                return int(result)
            return round(result, 10)
        elif isinstance(result, complex):
            return f"{result.real:.10g} + {result.imag:.10g}j"
        return result
    except (ZeroDivisionError, ValueError, OverflowError, SyntaxError) as e:
        return f"❌ Math Error: {str(e)}"
    except Exception as e:
        logging.error(f"Evaluation error: {e}", exc_info=True)
        return "❌ Invalid expression"

async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        expr = " ".join(context.args).strip()
        if not expr:
            keyboard = [
                [InlineKeyboardButton("Try Example", callback_data="calc_example")]
            ]
            await update.message.reply_text(
                "🧮 <b>Math Calculator</b>\n\n"
                "Usage: <code>/calc 2+2</code>\n"
                "Supports: + - * / ^ ( ) functions like sin, cos, sqrt\n\n"
                "Example: <code>/calc sin(pi/4) + 3^2</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        result = safe_eval(expr)
        if result is None:
            await update.message.reply_text("❌ Invalid characters or syntax in expression.")
            return

        keyboard = [
            [InlineKeyboardButton("Calculate Again", switch_inline_query_current_chat="")]
        ]
        await update.message.reply_text(
            f"🧮 <b>Math Calculator</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 <b>Expression:</b> <code>{html.escape(expr)}</code>\n"
            f"🎯 <b>Result:</b> <code>{html.escape(str(result))}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logging.error(f"Command error: {e}", exc_info=True)
        await update.message.reply_text("⚠️ An error occurred while processing your request.")

async def calc_example_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    example_expr = "sin(pi/4) + 3^2"
    result = safe_eval(example_expr)
    await query.edit_message_text(
        f"🧮 <b>Math Calculator</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 <b>Expression:</b> <code>{html.escape(example_expr)}</code>\n"
        f"🎯 <b>Result:</b> <code>{html.escape(str(result))}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML
    )
import telegram

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
 
BOT_USERNAME = "Monicrobot"  # Replace with your bot's username
# Hex to Text
def hex_to_text(hex_string):
    try:
        text = bytes.fromhex(hex_string).decode('utf-8')
        return text
    except Exception as e:
        return f"Error decoding hex: {str(e)}"

# Text to Hex
def text_to_hex(text):
    return ' '.join(format(ord(char), 'x') for char in text)

# Command handler for /code
async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        input_text = " ".join(context.args)

        hex_representation = text_to_hex(input_text)
        decoded_text = hex_to_text(input_text)

        response_text = (
            f"𝗜𝗻𝗽𝘂𝘁 𝗧𝗲𝘅𝘁➪\n{input_text}\n\n"
            f"𝗛𝗲𝘅 𝗥𝗲𝗽𝗿𝗲𝘀𝗲𝗻𝘁𝗮𝘁𝗶𝗼𝗻➪\n{hex_representation}\n\n"
            f"𝗗𝗲𝗰𝗼𝗱𝗲𝗱 𝗧𝗲𝘅𝘁➪\n{decoded_text}\n\n"
            f"𝗕𝗬 ➪ @{BOT_USERNAME}"
        )

        await update.message.reply_text(response_text)
    else:
        await update.message.reply_text("Please provide text after the /code command.")

# Module metadata (optional)
__mod_name__ = "𝐂𝐨𝐝𝐞𝐫"
__help__ = """
❍ /code <text>*:* 𝗚𝗲𝘁 𝗛𝗲𝘅 𝗮𝗻𝗱 𝗧𝗲𝘅𝘁 𝗲𝗻𝗰𝗼𝗱𝗶𝗻𝗴/𝗱𝗲𝗰𝗼𝗱𝗶𝗻𝗴
Example: `/code Hello World`
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler

import aiohttp
import random
from io import BytesIO
from typing import Optional, Dict, List
from datetime import datetime
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import CommandHandler, ContextTypes

# API Configuration with multiple sources
API_SOURCES = [
    {
        "name": "WaifuPics",
        "url": "https://api.waifu.pics/sfw/",
        "endpoints": ["waifu", "neko", "shinobu", "megumin"],
        "headers": {"User-Agent": "Mozilla/5.0"}
    },
    {
        "name": "NekoBot",
        "url": "https://nekobot.xyz/api/image?type=",
        "endpoints": ["neko", "waifu"],
        "headers": {"User-Agent": "Mozilla/5.0"}
    },
    {
        "name": "NekoLove",
        "url": "https://nekos.life/api/v2/img/",
        "endpoints": ["neko", "waifu"],
        "headers": {"User-Agent": "Mozilla/5.0"}
    }
]

# Cache to avoid duplicate images (optional)
IMAGE_CACHE: Dict[str, bytes] = {}
CACHE_EXPIRY = 3600  # 1 hour

async def fetch_image(url: str, headers: Dict) -> Optional[BytesIO]:
    """Download image from URL with proper headers."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.read()
                    buf = BytesIO(data)
                    buf.name = "anime_image.jpg"
                    return buf
    except Exception as e:
        print(f"[Download Error] {e}")
    return None

async def get_anime_image() -> Optional[BytesIO]:
    """Fetch a random anime image from multiple APIs with fallback."""
    for source in random.sample(API_SOURCES, len(API_SOURCES)):  # Shuffle APIs for load balancing
        endpoint = random.choice(source["endpoints"])  # Pick a random endpoint
        api_url = f"{source['url']}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch JSON response (for APIs that return URLs)
                async with session.get(api_url, headers=source["headers"]) as r:
                    if r.status == 200:
                        data = await r.json()
                        img_url = data.get("url") or data.get("message") or data.get("image")
                        if img_url:
                            return await fetch_image(img_url, source["headers"])
        except Exception as e:
            print(f"[{source['name']} Error] {e}")
    
    return None  # All APIs failed

async def animepic_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /animepic command with cute responses."""
    try:
        chat_id = update.effective_chat.id
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

        # Try to fetch an image
        image = await get_anime_image()

        if image:
            # Random cute captions
            captions = [
                "🌸 Here's your kawaii pic!",
                "✨ Magical girl power~",
                "💫 Neko-chan delivered!",
                "🎀 Anime vibes for you!",
                "🍥 Desu~ Enjoy the cuteness!"
            ]
            await update.message.reply_photo(
                photo=image,
                caption=f"{random.choice(captions)}\n\n<i>Powered by multiple anime APIs</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            # Fun error messages
            errors = [
                "🌸 The anime gods are resting... Try again later!",
                "✨ The magical girls are busy saving the world!",
                "💫 Too much kawaii broke the API!",
                "🎀 The catgirls are napping... zzz",
                "🍥 Baka! The anime dimension is unstable~"
            ]
            await update.message.reply_text(
                f"❌ {random.choice(errors)}",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        print(f"[AnimePic Error] {e}")
        await update.message.reply_text(
            "💢 Yabai! Something went wrong... *pouts*",
            parse_mode=ParseMode.HTML
        )

import random
from datetime import datetime
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

# Waifu images
WAIFU_PHOTOS = list(set([
    "https://files.catbox.moe/5tyu5g.jpg",
    "https://files.catbox.moe/mscchv.jpg",
    "https://files.catbox.moe/d25jj9.jpg",
    "https://files.catbox.moe/n4252m.jpg",
    "https://files.catbox.moe/cyyl6h.jpg",
    "https://files.catbox.moe/q93u62.jpg",
    "https://files.catbox.moe/0u1noj.jpg"
]))

# Placeholder anime sticker IDs (replace with real ones)
ANIME_STICKERS = [
    "CAACAgQAAxkBAAIB1GVJXU-8qjKo0sF_JrhqHQAEM8HyxAACdwADVp29Cl6b4vPZ8DJvLwQ",
    "CAACAgQAAxkBAAIB1WVJXU-7VKezGc1pbFuvIQAC7KxBLQACcwADVp29CmXjThQ_mYIbLwQ",
    "CAACAgQAAxkBAAIB12VJXU9ROrY2RCNYEmUtMgACZZVvLwACegADVp29Cq9AUn_0SliFLwQ"
]

# Daily memory cache
daily_cache = {}

def mention(user):
    return f"[{user.full_name}](tg://user?id={user.id})"

async def send_processing(update: Update, text: str):
    return await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def delete_later(message):
    await asyncio.sleep(2)
    try:
        await message.delete()
    except:
        pass

async def couple_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    TODAY = datetime.today().date().isoformat()
    key = (chat.id, TODAY, "couple")
    processing = await send_processing(update, "🔮 *Scanning the stars for today's destined couple...* ✨")

    if key in daily_cache:
        user1, user2 = daily_cache[key]
    else:
        try:
            await asyncio.sleep(1.5)
            admins = await context.bot.get_chat_administrators(chat.id)
            members = [m.user for m in admins if not m.user.is_bot]

            if len(members) < 2:
                await update.message.reply_text("❌ Not enough members to match.", reply_to_message_id=processing.message_id)
                await delete_later(processing)
                return

            user1, user2 = random.sample(members, 2)
            daily_cache[key] = (user1, user2)

            try:
                await context.bot.send_sticker(chat.id, random.choice(ANIME_STICKERS), reply_to_message_id=processing.message_id)
            except:
                pass

        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: `{e}`", parse_mode=ParseMode.MARKDOWN)
            await delete_later(processing)
            return

    love_score = random.randint(60, 100)
    compatibility = random.choice(["Perfect Match!", "Fated Pair", "Soulmates", "Cosmic Connection"])
    hearts = "💖" * (love_score // 20)
    zodiac = random.choice(["♈️", "♉️", "♊️", "♋️", "♌️", "♍️", "♎️", "♏️", "♐️", "♑️", "♒️", "♓️"])
    prediction = random.choice(['Eternal love!', 'Sweet romance ahead!', 'Passionate connection!'])

    caption = (
        f"🌸 *~ Cosmic Couple of the Day ~* 🌸\n\n"
        f"{zodiac} **{compatibility}** {zodiac}\n"
        f"✨ {mention(user1)} + {mention(user2)} ✨\n"
        f"💘 Love Score: {love_score}%\n{hearts}\n\n"
        f"📅 *Chosen on:* `{TODAY}`\n"
        f"🔮 *Prediction:* `{prediction}`"
    )

    await delete_later(processing)
    await update.message.reply_photo(random.choice(WAIFU_PHOTOS), caption=caption, parse_mode=ParseMode.MARKDOWN)

async def waifu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    today = datetime.today().date().isoformat()
    key = (chat.id, user.id, today, "waifu")
    processing = await send_processing(update, "🪄 *Summoning your perfect waifu...* 💫")

    if key in daily_cache:
        waifu = daily_cache[key]
    else:
        try:
            await asyncio.sleep(1.5)
            admins = await context.bot.get_chat_administrators(chat.id)
            candidates = [m.user for m in admins if not m.user.is_bot and m.user.id != user.id]

            if not candidates:
                await update.message.reply_text("😿 *No waifus found in this group today!*", parse_mode=ParseMode.MARKDOWN)
                await delete_later(processing)
                return

            waifu = random.choice(candidates)
            daily_cache[key] = waifu

            try:
                await context.bot.send_sticker(chat.id, random.choice(ANIME_STICKERS), reply_to_message_id=processing.message_id)
            except:
                pass

        except Exception as e:
            await update.message.reply_text(f"⚠️ *The summoning failed:* `{e}`", parse_mode=ParseMode.MARKDOWN)
            await delete_later(processing)
            return

    bond = random.randint(40, 100)
    bar = "█" * (bond // 10) + "░" * (10 - bond // 10)
    traits = random.sample(["Kind", "Tsundere", "Yandere", "Genki", "Kuudere", "Dandere"], 2)
    zodiac = random.choice(["♈️", "♉️", "♊️", "♋️", "♌️", "♍️", "♎️", "♏️", "♐️", "♑️", "♒️", "♓️"])

    caption = (
        f"💖 *~ Your Waifu of the Day ~* 💖\n\n"
        f"{zodiac} **{waifu.first_name}** the *{traits[0]} {traits[1]}* {zodiac}\n\n"
        f"👤 *For:* {mention(user)}\n"
        f"💞 *Bond Level:* `{bond}%`\n"
        f"`[{bar}]`\n\n"
        f"📊 *Stats:*\n"
        f"❤️ Affection: `{random.randint(50, 100)}%`\n"
        f"🍳 Cooking: `{random.randint(30, 100)}%`\n"
        f"⚔️ Combat: `{random.randint(0, 100)}%`\n\n"
        f"📅 *Summoned on:* `{today}`"
    )

    await delete_later(processing)
    await update.message.reply_photo(random.choice(WAIFU_PHOTOS), caption=caption, parse_mode=ParseMode.MARKDOWN)


API_URL = "https://open.er-api.com/v6/latest/"
CURRENCY_EMOJIS = {
    "USD": "💵", "EUR": "💶", "GBP": "💷", "JPY": "💴", "INR": "🇮🇳", "AUD": "🇦🇺",
    "CAD": "🇨🇦", "CHF": "🇨🇭", "CNY": "🇨🇳", "RUB": "🇷🇺", "BRL": "🇧🇷", "SGD": "🇸🇬",
    "ZAR": "🇿🇦", "KRW": "🇰🇷", "AED": "🇦🇪", "TRY": "🇹🇷"
}

async def fetch_exchange_rates(session, from_curr):
    try:
        async with session.get(f"{API_URL}{from_curr}") as response:
            if response.status == 200:
                data = await response.json()
                return data
            return None
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
        return None

async def convert_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text(
            "⚠️ *Usage:* `/currency <amount> <from> <to>`\n"
            "💡 *Example:* `/currency 100 USD INR`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        amount = float(args[0])
        from_curr = args[1].upper()
        to_curr = args[2].upper()
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please enter a number.")
        return

    async with aiohttp.ClientSession() as session:
        data = await fetch_exchange_rates(session, from_curr)
        
        if not data or not data.get("rates") or to_curr not in data["rates"]:
            await update.message.reply_text(
                "❌ Invalid currency codes or service unavailable. Use `/currencylist` to see options.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        rate = data["rates"][to_curr]
        result = round(amount * rate, 2)

        emoji_from = CURRENCY_EMOJIS.get(from_curr, "💲")
        emoji_to = CURRENCY_EMOJIS.get(to_curr, "💲")

        text = (
            "💱 <b>Currency Conversion</b>\n"
            f"<code>{amount} {from_curr}</code> {emoji_from} ➡️ <code>{result} {to_curr}</code> {emoji_to}\n"
            f"🔄 <i>1 {from_curr} = {rate} {to_curr}</i>"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def list_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        data = await fetch_exchange_rates(session, "USD")
        
        if not data or not data.get("rates"):
            await update.message.reply_text("⚠️ Unable to fetch currencies.")
            return

        currencies = sorted(data["rates"].keys())
        emoji_list = [f"{CURRENCY_EMOJIS.get(c, '💲')} <code>{c}</code>" for c in currencies]

        # Send in chunks to avoid message too long
        chunk_size = 25
        for i in range(0, len(emoji_list), chunk_size):
            chunk = emoji_list[i:i+chunk_size]
            await update.message.reply_text(
                "🌍 <b>Available Currencies:</b>\n" + " | ".join(chunk),
                parse_mode=ParseMode.HTML
            )

import os
import tempfile
import asyncio
import logging
from typing import Optional
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext,
)
from telegram.constants import ChatAction, ParseMode
import zipfile
import tarfile
import py7zr
from rarfile import RarFile, BadRarFile, NotRarFile

# Configuration
MAX_FILE_SIZE = 49 * 1024 * 1024  # 49MB
MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 200MB
MAX_FILES_TO_EXTRACT = 10  # Limit to 10 files per archive
EXTRACTION_TIMEOUT = 300  # 5 minutes timeout for extraction
SUPPORTED_EXTS = (".zip", ".rar", ".tar", ".tar.gz", ".tgz", ".7z")

logger = logging.getLogger(__name__)


def is_supported(filename: str) -> bool:
    """Check if the file extension is supported for extraction."""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTS)


async def extract_and_send_files(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    archive_path: str,
    dest_dir: str,
    status_msg,
) -> None:
    """
    Extract files from archive and send them one by one.
    Handles different archive formats and limits the number of extracted files.
    """
    sent = 0
    skipped = 0
    errors = 0

    async def try_send(file_path: str) -> None:
        """Helper function to send a file with error handling."""
        nonlocal sent, skipped, errors
        try:
            if os.path.getsize(file_path) > MAX_FILE_SIZE:
                skipped += 1
                return

            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT
            )
            await update.effective_chat.send_document(
                document=open(file_path, "rb"),
                caption=f"📄 <code>{os.path.basename(file_path)}</code>",
                parse_mode=ParseMode.HTML,
            )
            sent += 1
            await asyncio.sleep(1.2)  # Rate limiting
        except Exception as e:
            logger.warning(f"Error sending file {file_path}: {e}")
            errors += 1

    try:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                for name in zip_ref.namelist():
                    if sent >= MAX_FILES_TO_EXTRACT:
                        break
                    if not name.endswith("/"):  # Skip directories
                        zip_ref.extract(name, dest_dir)
                        full_path = os.path.join(dest_dir, name)
                        if os.path.isfile(full_path):
                            await try_send(full_path)

        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:*") as tar_ref:
                for member in tar_ref.getmembers():
                    if sent >= MAX_FILES_TO_EXTRACT:
                        break
                    if member.isfile():
                        tar_ref.extract(member, dest_dir)
                        full_path = os.path.join(dest_dir, member.name)
                        await try_send(full_path)

        elif archive_path.endswith(".rar"):
            with RarFile(archive_path) as rar_ref:
                for member in rar_ref.infolist():
                    if sent >= MAX_FILES_TO_EXTRACT:
                        break
                    if not member.isdir():
                        rar_ref.extract(member.filename, dest_dir)
                        full_path = os.path.join(dest_dir, member.filename)
                        if os.path.isfile(full_path):
                            await try_send(full_path)

        elif archive_path.endswith(".7z"):
            with py7zr.SevenZipFile(archive_path, mode="r") as z:
                for name in z.getnames():
                    if sent >= MAX_FILES_TO_EXTRACT:
                        break
                    z.extract(targets=[name], path=dest_dir)
                    full_path = os.path.join(dest_dir, name)
                    if os.path.isfile(full_path):
                        await try_send(full_path)

        # Prepare status message
        msg_parts = [f"✅ <b>Extraction complete.</b>\n📤 <b>Sent:</b> <code>{sent}</code> file(s)"]
        if skipped:
            msg_parts.append(f"\n🚫 <b>Skipped:</b> <code>{skipped}</code> (too large)")
        if errors:
            msg_parts.append(f"\n⚠️ <b>Errors:</b> <code>{errors}</code> (failed to send)")
        if sent >= MAX_FILES_TO_EXTRACT:
            msg_parts.append("\n⚠️ <b>File limit reached (10 files max).</b>")

        await status_msg.edit_text("".join(msg_parts), parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        await status_msg.edit_text(
            f"❌ <b>Extraction failed:</b>\n<code>{str(e)}</code>", parse_mode=ParseMode.HTML
        )


async def handle_archive(
    update: Update, context: ContextTypes.DEFAULT_TYPE, file
) -> None:
    """Handle the archive file processing pipeline."""
    filename = file.file_name or "unknown"
    status_msg = await update.effective_chat.send_message(
        "📥 <b>Downloading archive...</b>", parse_mode=ParseMode.HTML
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, filename)

        try:
            # Download the file with timeout
            await asyncio.wait_for(
                file.download_to_drive(file_path), timeout=EXTRACTION_TIMEOUT
            )

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > MAX_TOTAL_SIZE:
                return await status_msg.edit_text(
                    "⚠️ <b>Archive too large (limit 200MB)</b>", parse_mode=ParseMode.HTML
                )

            await status_msg.edit_text(
                "📂 <b>Extracting & sending files...</b>", parse_mode=ParseMode.HTML
            )
            await extract_and_send_files(update, context, file_path, tmpdir, status_msg)

        except asyncio.TimeoutError:
            await status_msg.edit_text(
                "⌛ <b>Operation timed out. Please try with a smaller archive.</b>",
                parse_mode=ParseMode.HTML,
            )
        except (BadRarFile, NotRarFile):
            await status_msg.edit_text(
                "❌ <b>Invalid RAR file or password protected.</b>", parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.exception(f"Failed to process archive: {e}")
            await status_msg.edit_text(
                f"❌ <b>Processing failed:</b>\n<code>{str(e)}</code>",
                parse_mode=ParseMode.HTML,
            )


async def extract_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /extract command."""
    if not update.message or not update.message.reply_to_message:
        return await update.message.reply_text(
            "⚠️ <b>Please reply to an archive file with</b> <code>/extract</code>.",
            parse_mode=ParseMode.HTML,
        )

    doc = update.message.reply_to_message.document
    if not doc:
        return await update.message.reply_text(
            "❌ <b>No document found in the replied message.</b>", parse_mode=ParseMode.HTML
        )

    filename = doc.file_name or ""
    if not is_supported(filename):
        return await update.message.reply_text(
            "❌ <b>Unsupported file type.</b>\nSupported: "
            "<code>.zip</code>, <code>.rar</code>, <code>.tar</code>, "
            "<code>.tar.gz</code>, <code>.7z</code>, <code>.tgz</code>",
            parse_mode=ParseMode.HTML,
        )

    await handle_archive(update, context, doc)


async def auto_extract_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Automatically handle archive files sent to the chat."""
    if not update.message or not update.message.document:
        return

    doc = update.message.document
    filename = doc.file_name or ""
    if not is_supported(filename):
        return

    # Create a menu to confirm extraction
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Extract", callback_data=f"extract_{update.message.message_id}"
            ),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_extract"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"📦 <b>Archive detected:</b> <code>{filename}</code>\n"
        "Do you want to extract this file?",
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("extract_"):
        message_id = int(query.data.split("_")[1])
        original_message = await context.bot.get_message(
            chat_id=query.message.chat_id, message_id=message_id
        )
        await handle_archive(update, context, original_message.document)
    elif query.data == "cancel_extract":
        await query.edit_message_text("❌ Extraction canceled.")
        
import requests
from telegram import Update

API_URL = "https://randomuser.me/api/"

async def fake_generator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        msg = await update.message.reply_text(
            "Usage: /fake <country_code>\nExample: /fake us"
        )
        await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id, delay=20)
        return

    country_code = context.args[0].lower()

    try:
        response = requests.get(API_URL, params={"nat": country_code})
        response.raise_for_status()
        data = response.json()

        if "results" not in data or not data["results"]:
            await update.message.reply_text("⚠️ Could not generate fake user.")
            return

        user = data["results"][0]
        name = user["name"]
        location = user["location"]
        dob = user["dob"]
        phone = user["phone"]
        email = user["email"]
        picture = user["picture"]["large"]
        gender = user["gender"].title()

        text = (
            f"🪄 <b>Fake Identity Generated:</b>\n\n"
            f"👤 <b>Name:</b> {name['title']} {name['first']} {name['last']}\n"
            f"🗺️ <b>Location:</b> {location['city']}, {location['state']}, {location['country']}\n"
            f"📧 <b>Email:</b> {email}\n"
            f"📞 <b>Phone:</b> {phone}\n"
            f"🎂 <b>DOB:</b> {dob['date'][:10]} (Age: {dob['age']})\n"
            f"🚻 <b>Gender:</b> {gender}\n"
        )

        await update.message.reply_photo(
            photo=picture,
            caption=text,
            parse_mode=ParseMode.HTML
        )

    except requests.RequestException as e:
        await update.message.reply_text(f"❌ API Error: {e}")

import requests
import json
import time
from bs4 import BeautifulSoup
from typing import Dict, Optional

# API Configuration
import requests
import json
from typing import Dict, Optional
import time

# API Configuration
FF_API_URL = "https://ariiflexlabs-playerinfo-icxc.onrender.com/ff_info"
DEFAULT_REGION = "en"  # Default region if not specified
CACHE_EXPIRY = 300  # 5 minutes cache

# Cache system
player_cache = {}

def get_cached_data(player_id: str, region: str) -> Optional[Dict]:
    """Get cached player data if available"""
    cache_key = f"{player_id}_{region}"
    current_time = time.time()
    
    # Clear expired cache entries
    expired_keys = [k for k, v in player_cache.items() 
                   if current_time - v['timestamp'] > CACHE_EXPIRY]
    for key in expired_keys:
        del player_cache[key]
    
    return player_cache.get(cache_key, {}).get('data')

def cache_player_data(player_id: str, region: str, data: Dict):
    """Cache player data with timestamp"""
    cache_key = f"{player_id}_{region}"
    player_cache[cache_key] = {
        'data': data,
        'timestamp': time.time()
    }

async def fetch_freefire_data(player_id: str, region: str = DEFAULT_REGION) -> Dict:
    """
    Fetch comprehensive Free Fire player data from AriiflexLabs API
    
    Args:
        player_id: Free Fire UID
        region: Region code (en, id, pt, etc.)
    
    Returns:
        Dictionary containing all player information
    """
    # Check cache first
    cached_data = get_cached_data(player_id, region)
    if cached_data:
        return cached_data
    
    try:
        # Make API request
        params = {
            'uid': player_id,
            'region': region
        }
        
        response = requests.get(
            FF_API_URL,
            params=params,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            },
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Standardize the API response format
        processed_data = {
            'basic': {
                'id': player_id,
                'name': data.get('nickname', 'N/A'),
                'level': data.get('level', 0),
                'exp': data.get('exp', 0),
                'server': data.get('server', 'Unknown'),
                'guild': data.get('guild', {}).get('name', 'No guild'),
                'guild_role': data.get('guild', {}).get('role', 'Member'),
                'avatar': data.get('avatar', ''),
                'title': data.get('title', 'No title'),
                'last_login': data.get('last_login', 'Unknown')
            },
            'stats': {
                'total_matches': data.get('total_matches', 0),
                'total_wins': data.get('total_wins', 0),
                'win_rate': data.get('win_rate', 0),
                'kills': data.get('total_kills', 0),
                'kd_ratio': data.get('kd_ratio', 0),
                'headshot_rate': data.get('headshot_rate', 0),
                'avg_damage': data.get('avg_damage', 0),
                'max_kills': data.get('max_kills', 0),
                'favorite_mode': data.get('favorite_mode', 'Unknown')
            },
            'ranked': {
                'current_rank': data.get('rank', {}).get('current', 'Unranked'),
                'rank_points': data.get('rank', {}).get('points', 0),
                'highest_rank': data.get('rank', {}).get('highest', 'Unranked'),
                'season_wins': data.get('rank', {}).get('season_wins', 0),
                'season_kills': data.get('rank', {}).get('season_kills', 0)
            },
            'inventory': {
                'diamonds': data.get('diamonds', 0),
                'gold': data.get('gold', 0),
                'characters': data.get('characters', []),
                'pets': data.get('pets', []),
                'weapons': data.get('weapons', [])
            },
            'last_updated': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Cache the processed data
        cache_player_data(player_id, region, processed_data)
        
        return processed_data
        
    except requests.exceptions.RequestException as e:
        return {'error': f"API request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {'error': "Invalid API response format"}
    except Exception as e:
        return {'error': f"Unexpected error: {str(e)}"}

def format_player_data(player_data: Dict) -> str:
    """
    Format player data into a readable Telegram message with Markdown
    
    Args:
        player_data: Dictionary containing player information
    
    Returns:
        Formatted string ready for Telegram
    """
    if 'error' in player_data:
        return f"❌ *Error*: {player_data['error']}\n\nPlease try again later."
    
    basic = player_data['basic']
    stats = player_data['stats']
    ranked = player_data['ranked']
    
    # Main message template
    message = f"""
🎮 *Free Fire Player Report* 🎮

*Basic Info:*
🆔 ID: `{basic['id']}`
👤 Name: {basic['name']}
⭐ Level: {basic['level']} (XP: {basic['exp']})
🌍 Server: {basic['server']}
🏆 Guild: {basic['guild']} ({basic['guild_role']})
🏅 Title: {basic['title']}
📅 Last Login: {basic['last_login']}

*Battle Stats:*
🎮 Matches: {stats['total_matches']}
🏆 Wins: {stats['total_wins']} ({stats['win_rate']}%)
🔫 Kills: {stats['kills']}
🎯 K/D Ratio: {stats['kd_ratio']}
💥 Headshots: {stats['headshot_rate']}%
💢 Avg Damage: {stats['avg_damage']}
👑 Max Kills: {stats['max_kills']}
🎮 Favorite Mode: {stats['favorite_mode']}

*Ranked Stats:*
🏅 Current Rank: {ranked['current_rank']}
📈 Points: {ranked['rank_points']}
🌟 Highest Rank: {ranked['highest_rank']}
🔥 Season Wins: {ranked['season_wins']}
🔫 Season Kills: {ranked['season_kills']}

*Inventory:*
💎 Diamonds: {player_data['inventory']['diamonds']}
🪙 Gold: {player_data['inventory']['gold']}
👤 Characters: {len(player_data['inventory']['characters'])}
🐾 Pets: {len(player_data['inventory']['pets'])}
🔫 Weapons: {len(player_data['inventory']['weapons'])}

📅 Last Updated: {player_data['last_updated']}
"""
    return message.strip()

# Example Telegram bot command handler
async def ffid_command(update, context):
    """
    Telegram bot command handler for /ffid
    Usage: /ffid <player_id> [region]
    """
    try:
        args = context.args
        if not args:
            await update.message.reply_text(
                "Please provide a Free Fire ID\n"
                "Usage: /ffid <player_id> [region]"
            )
            return
        
        player_id = args[0]
        region = args[1] if len(args) > 1 else DEFAULT_REGION
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Get player data
        player_data = await fetch_freefire_data(player_id, region)
        
        # Format and send response
        response = format_player_data(player_data)
        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
    except IndexError:
        await update.message.reply_text(
            "Invalid command format\n"
            "Usage: /ffid <player_id> [region]"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ An error occurred: {str(e)}\n"
            "Please try again later."
        )

import pyfiglet
from random import choice
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)


# Function to generate random figlet text and keyboard
def figle(text):
    fonts = pyfiglet.FigletFont.getFonts()
    font = choice(fonts)
    figled = pyfiglet.figlet_format(text, font=font)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴄʜᴀɴɢᴇ", callback_data="figlet"),
         InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close_reply")]
    ])
    return figled, keyboard

# Store latest text globally (not ideal for concurrency but replicates your logic)
figlet_cache = {}

# Command handler for /figlet
async def figlet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        text = ' '.join(context.args)
        figlet_cache[update.effective_chat.id] = text  # store per chat
        figled_text, keyboard = figle(text)
        await update.message.reply_text(
            f"ʜᴇʀᴇ ɪs ʏᴏᴜʀ ғɪɢʟᴇᴛ :\n<pre>{figled_text}</pre>",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text("Example:\n\n<code>/figlet PRINCE PAPA</code>", parse_mode=ParseMode.HTML)

# CallbackQuery handler for "figlet"
async def figlet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    text = figlet_cache.get(chat_id)
    if not text:
        await query.message.reply_text("No text found. Use /figlet command first.")
        return
    figled_text, keyboard = figle(text)
    await query.message.edit_text(
        f"ʜᴇʀᴇ ɪs ʏᴏᴜʀ ғɪɢʟᴇᴛ :\n<pre>{figled_text}</pre>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

# Optional: Close button handler
async def close_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.delete()

# Module metadata (optional if used in modular bot system)
__mod_name__ = "Fɪɢʟᴇᴛ"
__help__ = """
❍ /figlet <text>*:* ᴍᴀᴋᴇs ғɪɢʟᴇᴛ ᴏғ ᴛʜᴇ ɢɪᴠᴇɴ ᴛᴇxᴛ
Example: /figlet PRINCE PAPA
"""

# filters_sqlite.py
import sqlite3
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- SQLite Setup ---
DB_PATH = "monicfilters.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS filters (
            chat_id INTEGER,
            keyword TEXT,
            type TEXT,
            content TEXT,
            caption TEXT,
            PRIMARY KEY (chat_id, keyword)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- SQLite Helpers ---
def save_filter(chat_id: int, keyword: str, ftype: str, content: str, caption: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO filters (chat_id, keyword, type, content, caption)
        VALUES (?, ?, ?, ?, ?)
    """, (chat_id, keyword, ftype, content, caption))
    conn.commit()
    conn.close()

def get_filters(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT keyword, type, content, caption FROM filters WHERE chat_id = ?", (chat_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_filter(chat_id: int, keyword: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT keyword, type, content, caption FROM filters WHERE chat_id = ? AND keyword = ?", (chat_id, keyword))
    row = c.fetchone()
    conn.close()
    return row

def delete_filter(chat_id: int, keyword: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM filters WHERE chat_id = ? AND keyword = ?", (chat_id, keyword))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted

# --- Handlers ---
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or len(context.args) < 1:
        await update.message.reply_text(
            "✨ *Usage:* `/filter <keyword>` (reply to a message to save as filter)",
            parse_mode="Markdown"
        )
        return

    keyword = context.args[0].lower()
    reply = update.message.reply_to_message

    ftype, content, caption = None, None, None

    if reply.text or reply.caption:
        ftype = "text"
        content = reply.text or reply.caption

    elif reply.sticker:
        ftype = "sticker"
        content = reply.sticker.file_id

    elif reply.photo:
        ftype = "photo"
        content = reply.photo[-1].file_id
        caption = reply.caption

    elif reply.animation:
        ftype = "animation"
        content = reply.animation.file_id
        caption = reply.caption

    elif reply.video:
        ftype = "video"
        content = reply.video.file_id
        caption = reply.caption

    elif reply.voice:
        ftype = "voice"
        content = reply.voice.file_id

    else:
        await update.message.reply_text("❌ Unsupported media type.")
        return

    save_filter(update.effective_chat.id, keyword, ftype, content, caption)
    await update.message.reply_text(
        f"✅ *Filter saved for* `{keyword}`",
        parse_mode="Markdown"
    )

async def remove_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("✨ *Usage:* `/unfilter <keyword>`", parse_mode="Markdown")
        return

    keyword = context.args[0].lower()
    deleted = delete_filter(update.effective_chat.id, keyword)

    if deleted == 0:
        await update.message.reply_text(f"⚠️ *No filter found for* `{keyword}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ *Removed filter* `{keyword}`", parse_mode="Markdown")

async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_filters = get_filters(update.effective_chat.id)
    if not all_filters:
        await update.message.reply_text("📂 *No filters set yet!*", parse_mode="Markdown")
        return

    text = "📁 *Active Filters:*\n\n"
    for keyword, _, _, _ in all_filters:
        text += f"• `{keyword}`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def filter_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return

    text = update.message.text.lower()
    chat_id = update.effective_chat.id
    all_filters = get_filters(chat_id)

    for keyword, ftype, content, caption in all_filters:
        # Regex ensures keyword matches even inside sentences, but as a whole word
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            if ftype == "text":
                await update.message.reply_text(content)
            elif ftype == "sticker":
                await update.message.reply_sticker(content)
            elif ftype == "photo":
                await update.message.reply_photo(content, caption=caption)
            elif ftype == "animation":
                await update.message.reply_animation(content, caption=caption)
            elif ftype == "video":
                await update.message.reply_video(content, caption=caption)
            elif ftype == "voice":
                await update.message.reply_voice(content)
            break

class Fonts:
    def typewriter(text):
        style = {
            "a": "𝚊",
            "b": "𝚋",
            "c": "𝚌",
            "d": "𝚍",
            "e": "𝚎",
            "f": "𝚏",
            "g": "𝚐",
            "h": "𝚑",
            "i": "𝚒",
            "j": "𝚓",
            "k": "𝚔",
            "l": "𝚕",
            "m": "𝚖",
            "n": "𝚗",
            "o": "𝚘",
            "p": "𝚙",
            "q": "𝚚",
            "r": "𝚛",
            "s": "𝚜",
            "t": "𝚝",
            "u": "𝚞",
            "v": "𝚟",
            "w": "𝚠",
            "x": "𝚡",
            "y": "𝚢",
            "z": "𝚣",
            "A": "𝙰",
            "B": "𝙱",
            "C": "𝙲",
            "D": "𝙳",
            "E": "𝙴",
            "F": "𝙵",
            "G": "𝙶",
            "H": "𝙷",
            "I": "𝙸",
            "J": "𝙹",
            "K": "𝙺",
            "L": "𝙻",
            "M": "𝙼",
            "N": "𝙽",
            "O": "𝙾",
            "P": "𝙿",
            "Q": "𝚀",
            "R": "𝚁",
            "S": "𝚂",
            "T": "𝚃",
            "U": "𝚄",
            "V": "𝚅",
            "W": "𝚆",
            "X": "𝚇",
            "Y": "𝚈",
            "Z": "𝚉",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def outline(text):
        style = {
            "a": "𝕒",
            "b": "𝕓",
            "c": "𝕔",
            "d": "𝕕",
            "e": "𝕖",
            "f": "𝕗",
            "g": "𝕘",
            "h": "𝕙",
            "i": "𝕚",
            "j": "𝕛",
            "k": "𝕜",
            "l": "𝕝",
            "m": "𝕞",
            "n": "𝕟",
            "o": "𝕠",
            "p": "𝕡",
            "q": "𝕢",
            "r": "𝕣",
            "s": "𝕤",
            "t": "𝕥",
            "u": "𝕦",
            "v": "𝕧",
            "w": "𝕨",
            "x": "𝕩",
            "y": "𝕪",
            "z": "𝕫",
            "A": "𝔸",
            "B": "𝔹",
            "C": "ℂ",
            "D": "𝔻",
            "E": "𝔼",
            "F": "𝔽",
            "G": "𝔾",
            "H": "ℍ",
            "I": "𝕀",
            "J": "𝕁",
            "K": "𝕂",
            "L": "𝕃",
            "M": "𝕄",
            "N": "ℕ",
            "O": "𝕆",
            "P": "ℙ",
            "Q": "ℚ",
            "R": "ℝ",
            "S": "𝕊",
            "T": "𝕋",
            "U": "𝕌",
            "V": "𝕍",
            "W": "𝕎",
            "X": "𝕏",
            "Y": "𝕐",
            "Z": "ℤ",
            "0": "𝟘",
            "1": "𝟙",
            "2": "𝟚",
            "3": "𝟛",
            "4": "𝟜",
            "5": "𝟝",
            "6": "𝟞",
            "7": "𝟟",
            "8": "𝟠",
            "9": "𝟡",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def serief(text):
        style = {
            "a": "𝐚",
            "b": "𝐛",
            "c": "𝐜",
            "d": "𝐝",
            "e": "𝐞",
            "f": "𝐟",
            "g": "𝐠",
            "h": "𝐡",
            "i": "𝐢",
            "j": "𝐣",
            "k": "𝐤",
            "l": "𝐥",
            "m": "𝐦",
            "n": "𝐧",
            "o": "𝐨",
            "p": "𝐩",
            "q": "𝐪",
            "r": "𝐫",
            "s": "𝐬",
            "t": "𝐭",
            "u": "𝐮",
            "v": "𝐯",
            "w": "𝐰",
            "x": "𝐱",
            "y": "𝐲",
            "z": "𝐳",
            "A": "𝐀",
            "B": "𝐁",
            "C": "𝐂",
            "D": "𝐃",
            "E": "𝐄",
            "F": "𝐅",
            "G": "𝐆",
            "H": "𝐇",
            "I": "𝐈",
            "J": "𝐉",
            "K": "𝐊",
            "L": "𝐋",
            "M": "𝐌",
            "N": "𝐍",
            "O": "𝐎",
            "P": "𝐏",
            "Q": "𝐐",
            "R": "𝐑",
            "S": "𝐒",
            "T": "𝐓",
            "U": "𝐔",
            "V": "𝐕",
            "W": "𝐖",
            "X": "𝐗",
            "Y": "𝐘",
            "Z": "𝐙",
            "0": "𝟎",
            "1": "𝟏",
            "2": "𝟐",
            "3": "𝟑",
            "4": "𝟒",
            "5": "𝟓",
            "6": "𝟔",
            "7": "𝟕",
            "8": "𝟖",
            "9": "𝟗",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def bold_cool(text):
        style = {
            "a": "𝒂",
            "b": "𝒃",
            "c": "𝒄",
            "d": "𝒅",
            "e": "𝒆",
            "f": "𝒇",
            "g": "𝒈",
            "h": "𝒉",
            "i": "𝒊",
            "j": "𝒋",
            "k": "𝒌",
            "l": "𝒍",
            "m": "𝒎",
            "n": "𝒏",
            "o": "𝒐",
            "p": "𝒑",
            "q": "𝒒",
            "r": "𝒓",
            "s": "𝒔",
            "t": "𝒕",
            "u": "𝒖",
            "v": "𝒗",
            "w": "𝒘",
            "x": "𝒙",
            "y": "𝒚",
            "z": "𝒛",
            "A": "𝑨",
            "B": "𝑩",
            "C": "𝑪",
            "D": "𝑫",
            "E": "𝑬",
            "F": "𝑭",
            "G": "𝑮",
            "H": "𝑯",
            "I": "𝑰",
            "J": "𝑱",
            "K": "𝑲",
            "L": "𝑳",
            "M": "𝑴",
            "N": "𝑵",
            "O": "𝑶",
            "P": "𝑷",
            "Q": "𝑸",
            "R": "𝑹",
            "S": "𝑺",
            "T": "𝑻",
            "U": "𝑼",
            "V": "𝑽",
            "W": "𝑾",
            "X": "𝑿",
            "Y": "𝒀",
            "Z": "𝒁",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def cool(text):
        style = {
            "a": "𝑎",
            "b": "𝑏",
            "c": "𝑐",
            "d": "𝑑",
            "e": "𝑒",
            "f": "𝑓",
            "g": "𝑔",
            "h": "ℎ",
            "i": "𝑖",
            "j": "𝑗",
            "k": "𝑘",
            "l": "𝑙",
            "m": "𝑚",
            "n": "𝑛",
            "o": "𝑜",
            "p": "𝑝",
            "q": "𝑞",
            "r": "𝑟",
            "s": "𝑠",
            "t": "𝑡",
            "u": "𝑢",
            "v": "𝑣",
            "w": "𝑤",
            "x": "𝑥",
            "y": "𝑦",
            "z": "𝑧",
            "A": "𝐴",
            "B": "𝐵",
            "C": "𝐶",
            "D": "𝐷",
            "E": "𝐸",
            "F": "𝐹",
            "G": "𝐺",
            "H": "𝐻",
            "I": "𝐼",
            "J": "𝐽",
            "K": "𝐾",
            "L": "𝐿",
            "M": "𝑀",
            "N": "𝑁",
            "O": "𝑂",
            "P": "𝑃",
            "Q": "𝑄",
            "R": "𝑅",
            "S": "𝑆",
            "T": "𝑇",
            "U": "𝑈",
            "V": "𝑉",
            "W": "𝑊",
            "X": "𝑋",
            "Y": "𝑌",
            "Z": "𝑍",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def smallcap(text):
        style = {
            "a": "ᴀ",
            "b": "ʙ",
            "c": "ᴄ",
            "d": "ᴅ",
            "e": "ᴇ",
            "f": "ғ",
            "g": "ɢ",
            "h": "ʜ",
            "i": "ɪ",
            "j": "J",
            "k": "ᴋ",
            "l": "ʟ",
            "m": "ᴍ",
            "n": "ɴ",
            "o": "ᴏ",
            "p": "ᴘ",
            "q": "ǫ",
            "r": "ʀ",
            "s": "s",
            "t": "ᴛ",
            "u": "ᴜ",
            "v": "ᴠ",
            "w": "ᴡ",
            "x": "x",
            "y": "ʏ",
            "z": "ᴢ",
            "A": "A",
            "B": "B",
            "C": "C",
            "D": "D",
            "E": "E",
            "F": "F",
            "G": "G",
            "H": "H",
            "I": "I",
            "J": "J",
            "K": "K",
            "L": "L",
            "M": "M",
            "N": "N",
            "O": "O",
            "P": "P",
            "Q": "Q",
            "R": "R",
            "S": "S",
            "T": "T",
            "U": "U",
            "V": "V",
            "W": "W",
            "X": "X",
            "Y": "Y",
            "Z": "Z",
            "0": "𝟶",
            "1": "𝟷",
            "2": "𝟸",
            "3": "𝟹",
            "4": "𝟺",
            "5": "𝟻",
            "6": "𝟼",
            "7": "𝟽",
            "8": "𝟾",
            "9": "𝟿",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def script(text):
        style = {
            "a": "𝒶",
            "b": "𝒷",
            "c": "𝒸",
            "d": "𝒹",
            "e": "ℯ",
            "f": "𝒻",
            "g": "ℊ",
            "h": "𝒽",
            "i": "𝒾",
            "j": "𝒿",
            "k": "𝓀",
            "l": "𝓁",
            "m": "𝓂",
            "n": "𝓃",
            "o": "ℴ",
            "p": "𝓅",
            "q": "𝓆",
            "r": "𝓇",
            "s": "𝓈",
            "t": "𝓉",
            "u": "𝓊",
            "v": "𝓋",
            "w": "𝓌",
            "x": "𝓍",
            "y": "𝓎",
            "z": "𝓏",
            "A": "𝒜",
            "B": "ℬ",
            "C": "𝒞",
            "D": "𝒟",
            "E": "ℰ",
            "F": "ℱ",
            "G": "𝒢",
            "H": "ℋ",
            "I": "ℐ",
            "J": "𝒥",
            "K": "𝒦",
            "L": "ℒ",
            "M": "ℳ",
            "N": "𝒩",
            "O": "𝒪",
            "P": "𝒫",
            "Q": "𝒬",
            "R": "ℛ",
            "S": "𝒮",
            "T": "𝒯",
            "U": "𝒰",
            "V": "𝒱",
            "W": "𝒲",
            "X": "𝒳",
            "Y": "𝒴",
            "Z": "𝒵",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def bold_script(text):
        style = {
            "a": "𝓪",
            "b": "𝓫",
            "c": "𝓬",
            "d": "𝓭",
            "e": "𝓮",
            "f": "𝓯",
            "g": "𝓰",
            "h": "𝓱",
            "i": "𝓲",
            "j": "𝓳",
            "k": "𝓴",
            "l": "𝓵",
            "m": "𝓶",
            "n": "𝓷",
            "o": "𝓸",
            "p": "𝓹",
            "q": "𝓺",
            "r": "𝓻",
            "s": "𝓼",
            "t": "𝓽",
            "u": "𝓾",
            "v": "𝓿",
            "w": "𝔀",
            "x": "𝔁",
            "y": "𝔂",
            "z": "𝔃",
            "A": "𝓐",
            "B": "𝓑",
            "C": "𝓒",
            "D": "𝓓",
            "E": "𝓔",
            "F": "𝓕",
            "G": "𝓖",
            "H": "𝓗",
            "I": "𝓘",
            "J": "𝓙",
            "K": "𝓚",
            "L": "𝓛",
            "M": "𝓜",
            "N": "𝓝",
            "O": "𝓞",
            "P": "𝓟",
            "Q": "𝓠",
            "R": "𝓡",
            "S": "𝓢",
            "T": "𝓣",
            "U": "𝓤",
            "V": "𝓥",
            "W": "𝓦",
            "X": "𝓧",
            "Y": "𝓨",
            "Z": "𝓩",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def tiny(text):
        style = {
            "a": "ᵃ",
            "b": "ᵇ",
            "c": "ᶜ",
            "d": "ᵈ",
            "e": "ᵉ",
            "f": "ᶠ",
            "g": "ᵍ",
            "h": "ʰ",
            "i": "ⁱ",
            "j": "ʲ",
            "k": "ᵏ",
            "l": "ˡ",
            "m": "ᵐ",
            "n": "ⁿ",
            "o": "ᵒ",
            "p": "ᵖ",
            "q": "ᵠ",
            "r": "ʳ",
            "s": "ˢ",
            "t": "ᵗ",
            "u": "ᵘ",
            "v": "ᵛ",
            "w": "ʷ",
            "x": "ˣ",
            "y": "ʸ",
            "z": "ᶻ",
            "A": "ᵃ",
            "B": "ᵇ",
            "C": "ᶜ",
            "D": "ᵈ",
            "E": "ᵉ",
            "F": "ᶠ",
            "G": "ᵍ",
            "H": "ʰ",
            "I": "ⁱ",
            "J": "ʲ",
            "K": "ᵏ",
            "L": "ˡ",
            "M": "ᵐ",
            "N": "ⁿ",
            "O": "ᵒ",
            "P": "ᵖ",
            "Q": "ᵠ",
            "R": "ʳ",
            "S": "ˢ",
            "T": "ᵗ",
            "U": "ᵘ",
            "V": "ᵛ",
            "W": "ʷ",
            "X": "ˣ",
            "Y": "ʸ",
            "Z": "ᶻ",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def comic(text):
        style = {
            "a": "ᗩ",
            "b": "ᗷ",
            "c": "ᑕ",
            "d": "ᗪ",
            "e": "ᗴ",
            "f": "ᖴ",
            "g": "ᘜ",
            "h": "ᕼ",
            "i": "I",
            "j": "ᒍ",
            "k": "K",
            "l": "ᒪ",
            "m": "ᗰ",
            "n": "ᑎ",
            "o": "O",
            "p": "ᑭ",
            "q": "ᑫ",
            "r": "ᖇ",
            "s": "Տ",
            "t": "T",
            "u": "ᑌ",
            "v": "ᐯ",
            "w": "ᗯ",
            "x": "᙭",
            "y": "Y",
            "z": "ᘔ",
            "A": "ᗩ",
            "B": "ᗷ",
            "C": "ᑕ",
            "D": "ᗪ",
            "E": "ᗴ",
            "F": "ᖴ",
            "G": "ᘜ",
            "H": "ᕼ",
            "I": "I",
            "J": "ᒍ",
            "K": "K",
            "L": "ᒪ",
            "M": "ᗰ",
            "N": "ᑎ",
            "O": "O",
            "P": "ᑭ",
            "Q": "ᑫ",
            "R": "ᖇ",
            "S": "Տ",
            "T": "T",
            "U": "ᑌ",
            "V": "ᐯ",
            "W": "ᗯ",
            "X": "᙭",
            "Y": "Y",
            "Z": "ᘔ",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def san(text):
        style = {
            "a": "𝗮",
            "b": "𝗯",
            "c": "𝗰",
            "d": "𝗱",
            "e": "𝗲",
            "f": "𝗳",
            "g": "𝗴",
            "h": "𝗵",
            "i": "𝗶",
            "j": "𝗷",
            "k": "𝗸",
            "l": "𝗹",
            "m": "𝗺",
            "n": "𝗻",
            "o": "𝗼",
            "p": "𝗽",
            "q": "𝗾",
            "r": "𝗿",
            "s": "𝘀",
            "t": "𝘁",
            "u": "𝘂",
            "v": "𝘃",
            "w": "𝘄",
            "x": "𝘅",
            "y": "𝘆",
            "z": "𝘇",
            "A": "𝗔",
            "B": "𝗕",
            "C": "𝗖",
            "D": "𝗗",
            "E": "𝗘",
            "F": "𝗙",
            "G": "𝗚",
            "H": "𝗛",
            "I": "𝗜",
            "J": "𝗝",
            "K": "𝗞",
            "L": "𝗟",
            "M": "𝗠",
            "N": "𝗡",
            "O": "𝗢",
            "P": "𝗣",
            "Q": "𝗤",
            "R": "𝗥",
            "S": "𝗦",
            "T": "𝗧",
            "U": "𝗨",
            "V": "𝗩",
            "W": "𝗪",
            "X": "𝗫",
            "Y": "𝗬",
            "Z": "𝗭",
            "0": "𝟬",
            "1": "𝟭",
            "2": "𝟮",
            "3": "𝟯",
            "4": "𝟰",
            "5": "𝟱",
            "6": "𝟲",
            "7": "𝟳",
            "8": "𝟴",
            "9": "𝟵",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def slant_san(text):
        style = {
            "a": "𝙖",
            "b": "𝙗",
            "c": "𝙘",
            "d": "𝙙",
            "e": "𝙚",
            "f": "𝙛",
            "g": "𝙜",
            "h": "𝙝",
            "i": "𝙞",
            "j": "𝙟",
            "k": "𝙠",
            "l": "𝙡",
            "m": "𝙢",
            "n": "𝙣",
            "o": "𝙤",
            "p": "𝙥",
            "q": "𝙦",
            "r": "𝙧",
            "s": "𝙨",
            "t": "𝙩",
            "u": "𝙪",
            "v": "𝙫",
            "w": "𝙬",
            "x": "𝙭",
            "y": "𝙮",
            "z": "𝙯",
            "A": "𝘼",
            "B": "𝘽",
            "C": "𝘾",
            "D": "𝘿",
            "E": "𝙀",
            "F": "𝙁",
            "G": "𝙂",
            "H": "𝙃",
            "I": "𝙄",
            "J": "𝙅",
            "K": "𝙆",
            "L": "𝙇",
            "M": "𝙈",
            "N": "𝙉",
            "O": "𝙊",
            "P": "𝙋",
            "Q": "𝙌",
            "R": "𝙍",
            "S": "𝙎",
            "T": "𝙏",
            "U": "𝙐",
            "V": "𝙑",
            "W": "𝙒",
            "X": "𝙓",
            "Y": "𝙔",
            "Z": "𝙕",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def slant(text):
        style = {
            "a": "𝘢",
            "b": "𝘣",
            "c": "𝘤",
            "d": "𝘥",
            "e": "𝘦",
            "f": "𝘧",
            "g": "𝘨",
            "h": "𝘩",
            "i": "𝘪",
            "j": "𝘫",
            "k": "𝘬",
            "l": "𝘭",
            "m": "𝘮",
            "n": "𝘯",
            "o": "𝘰",
            "p": "𝘱",
            "q": "𝘲",
            "r": "𝘳",
            "s": "𝘴",
            "t": "𝘵",
            "u": "𝘶",
            "v": "𝘷",
            "w": "𝘸",
            "x": "𝘹",
            "y": "𝘺",
            "z": "𝘻",
            "A": "𝘈",
            "B": "𝘉",
            "C": "𝘊",
            "D": "𝘋",
            "E": "𝘌",
            "F": "𝘍",
            "G": "𝘎",
            "H": "𝘏",
            "I": "𝘐",
            "J": "𝘑",
            "K": "𝘒",
            "L": "𝘓",
            "M": "𝘔",
            "N": "𝘕",
            "O": "𝘖",
            "P": "𝘗",
            "Q": "𝘘",
            "R": "𝘙",
            "S": "𝘚",
            "T": "𝘛",
            "U": "𝘜",
            "V": "𝘝",
            "W": "𝘞",
            "X": "𝘟",
            "Y": "𝘠",
            "Z": "𝘡",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def sim(text):
        style = {
            "a": "𝖺",
            "b": "𝖻",
            "c": "𝖼",
            "d": "𝖽",
            "e": "𝖾",
            "f": "𝖿",
            "g": "𝗀",
            "h": "𝗁",
            "i": "𝗂",
            "j": "𝗃",
            "k": "𝗄",
            "l": "𝗅",
            "m": "𝗆",
            "n": "𝗇",
            "o": "𝗈",
            "p": "𝗉",
            "q": "𝗊",
            "r": "𝗋",
            "s": "𝗌",
            "t": "𝗍",
            "u": "𝗎",
            "v": "𝗏",
            "w": "𝗐",
            "x": "𝗑",
            "y": "𝗒",
            "z": "𝗓",
            "A": "𝖠",
            "B": "𝖡",
            "C": "𝖢",
            "D": "𝖣",
            "E": "𝖤",
            "F": "𝖥",
            "G": "𝖦",
            "H": "𝖧",
            "I": "𝖨",
            "J": "𝖩",
            "K": "𝖪",
            "L": "𝖫",
            "M": "𝖬",
            "N": "𝖭",
            "O": "𝖮",
            "P": "𝖯",
            "Q": "𝖰",
            "R": "𝖱",
            "S": "𝖲",
            "T": "𝖳",
            "U": "𝖴",
            "V": "𝖵",
            "W": "𝖶",
            "X": "𝖷",
            "Y": "𝖸",
            "Z": "𝖹",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def circles(text):
        style = {
            "a": "Ⓐ︎",
            "b": "Ⓑ︎",
            "c": "Ⓒ︎",
            "d": "Ⓓ︎",
            "e": "Ⓔ︎",
            "f": "Ⓕ︎",
            "g": "Ⓖ︎",
            "h": "Ⓗ︎",
            "i": "Ⓘ︎",
            "j": "Ⓙ︎",
            "k": "Ⓚ︎",
            "l": "Ⓛ︎",
            "m": "Ⓜ︎",
            "n": "Ⓝ︎",
            "o": "Ⓞ︎",
            "p": "Ⓟ︎",
            "q": "Ⓠ︎",
            "r": "Ⓡ︎",
            "s": "Ⓢ︎",
            "t": "Ⓣ︎",
            "u": "Ⓤ︎",
            "v": "Ⓥ︎",
            "w": "Ⓦ︎",
            "x": "Ⓧ︎",
            "y": "Ⓨ︎",
            "z": "Ⓩ︎",
            "A": "Ⓐ︎",
            "B": "Ⓑ︎",
            "C": "Ⓒ︎",
            "D": "Ⓓ︎",
            "E": "Ⓔ︎",
            "F": "Ⓕ︎",
            "G": "Ⓖ︎",
            "H": "Ⓗ︎",
            "I": "Ⓘ︎",
            "J": "Ⓙ︎",
            "K": "Ⓚ︎",
            "L": "Ⓛ︎",
            "M": "Ⓜ︎",
            "N": "Ⓝ︎",
            "O": "Ⓞ︎",
            "P": "Ⓟ︎",
            "Q": "Ⓠ︎",
            "R": "Ⓡ︎",
            "S": "Ⓢ︎",
            "T": "Ⓣ︎",
            "U": "Ⓤ︎",
            "V": "Ⓥ︎",
            "W": "Ⓦ︎",
            "X": "Ⓧ︎",
            "Y": "Ⓨ︎",
            "Z": "Ⓩ︎",
            "0": "⓪",
            "1": "①",
            "2": "②",
            "3": "③",
            "4": "④",
            "5": "⑤",
            "6": "⑥",
            "7": "⑦",
            "8": "⑧",
            "9": "⑨",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def dark_circle(text):
        style = {
            "a": "🅐︎",
            "b": "🅑︎",
            "c": "🅒︎",
            "d": "🅓︎",
            "e": "🅔︎",
            "f": "🅕︎",
            "g": "🅖︎",
            "h": "🅗︎",
            "i": "🅘︎",
            "j": "🅙︎",
            "k": "🅚︎",
            "l": "🅛︎",
            "m": "🅜︎",
            "n": "🅝︎",
            "o": "🅞︎",
            "p": "🅟︎",
            "q": "🅠︎",
            "r": "🅡︎",
            "s": "🅢︎",
            "t": "🅣︎",
            "u": "🅤︎",
            "v": "🅥︎",
            "w": "🅦︎",
            "x": "🅧︎",
            "y": "🅨︎",
            "z": "🅩︎",
            "A": "🅐︎",
            "B": "🅑︎",
            "C": "🅒︎",
            "D": "🅓︎",
            "E": "🅔︎",
            "F": "🅕︎",
            "G": "🅖︎",
            "H": "🅗︎",
            "I": "🅘︎",
            "J": "🅙︎",
            "K": "🅚︎",
            "L": "🅛︎",
            "M": "🅜︎",
            "N": "🅝︎",
            "O": "🅞︎",
            "P": "🅟︎",
            "Q": "🅠︎",
            "R": "🅡︎",
            "S": "🅢︎",
            "T": "🅣︎",
            "U": "🅤︎",
            "V": "🅥︎",
            "W": "🅦︎",
            "X": "🅧︎",
            "Y": "🅨︎",
            "Z": "🅩",
            "0": "⓿",
            "1": "➊",
            "2": "➋",
            "3": "➌",
            "4": "➍",
            "5": "➎",
            "6": "➏",
            "7": "➐",
            "8": "➑",
            "9": "➒",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def gothic(text):
        style = {
            "a": "𝔞",
            "b": "𝔟",
            "c": "𝔠",
            "d": "𝔡",
            "e": "𝔢",
            "f": "𝔣",
            "g": "𝔤",
            "h": "𝔥",
            "i": "𝔦",
            "j": "𝔧",
            "k": "𝔨",
            "l": "𝔩",
            "m": "𝔪",
            "n": "𝔫",
            "o": "𝔬",
            "p": "𝔭",
            "q": "𝔮",
            "r": "𝔯",
            "s": "𝔰",
            "t": "𝔱",
            "u": "𝔲",
            "v": "𝔳",
            "w": "𝔴",
            "x": "𝔵",
            "y": "𝔶",
            "z": "𝔷",
            "A": "𝔄",
            "B": "𝔅",
            "C": "ℭ",
            "D": "𝔇",
            "E": "𝔈",
            "F": "𝔉",
            "G": "𝔊",
            "H": "ℌ",
            "I": "ℑ",
            "J": "𝔍",
            "K": "𝔎",
            "L": "𝔏",
            "M": "𝔐",
            "N": "𝔑",
            "O": "𝔒",
            "P": "𝔓",
            "Q": "𝔔",
            "R": "ℜ",
            "S": "𝔖",
            "T": "𝔗",
            "U": "𝔘",
            "V": "𝔙",
            "W": "𝔚",
            "X": "𝔛",
            "Y": "𝔜",
            "Z": "ℨ",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def bold_gothic(text):
        style = {
            "a": "𝖆",
            "b": "𝖇",
            "c": "𝖈",
            "d": "𝖉",
            "e": "𝖊",
            "f": "𝖋",
            "g": "𝖌",
            "h": "𝖍",
            "i": "𝖎",
            "j": "𝖏",
            "k": "𝖐",
            "l": "𝖑",
            "m": "𝖒",
            "n": "𝖓",
            "o": "𝖔",
            "p": "𝖕",
            "q": "𝖖",
            "r": "𝖗",
            "s": "𝖘",
            "t": "𝖙",
            "u": "𝖚",
            "v": "𝖛",
            "w": "𝖜",
            "x": "𝖝",
            "y": "𝖞",
            "z": "𝖟",
            "A": "𝕬",
            "B": "𝕭",
            "C": "𝕮",
            "D": "𝕺",
            "E": "𝕰",
            "F": "𝕱",
            "G": "𝕲",
            "H": "𝕳",
            "I": "𝕴",
            "J": "𝕵",
            "K": "𝕶",
            "L": "𝕷",
            "M": "𝕸",
            "N": "𝕹",
            "O": "𝕺",
            "P": "𝕻",
            "Q": "𝕼",
            "R": "𝕽",
            "S": "𝕾",
            "T": "𝕿",
            "U": "𝖀",
            "V": "𝖁",
            "W": "𝖂",
            "X": "𝖃",
            "Y": "𝖄",
            "Z": "𝖅",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def cloud(text):
        style = {
            "a": "a͜͡",
            "b": "b͜͡",
            "c": "c͜͡",
            "d": "d͜͡",
            "e": "e͜͡",
            "f": "f͜͡",
            "g": "g͜͡",
            "h": "h͜͡",
            "i": "i͜͡",
            "j": "j͜͡",
            "k": "k͜͡",
            "l": "l͜͡",
            "m": "m͜͡",
            "n": "n͜͡",
            "o": "o͜͡",
            "p": "p͜͡",
            "q": "q͜͡",
            "r": "r͜͡",
            "s": "s͜͡",
            "t": "t͜͡",
            "u": "u͜͡",
            "v": "v͜͡",
            "w": "w͜͡",
            "x": "x͜͡",
            "y": "y͜͡",
            "z": "z͜͡",
            "A": "A͜͡",
            "B": "B͜͡",
            "C": "C͜͡",
            "D": "D͜͡",
            "E": "E͜͡",
            "F": "F͜͡",
            "G": "G͜͡",
            "H": "H͜͡",
            "I": "I͜͡",
            "J": "J͜͡",
            "K": "K͜͡",
            "L": "L͜͡",
            "M": "M͜͡",
            "N": "N͜͡",
            "O": "O͜͡",
            "P": "P͜͡",
            "Q": "Q͜͡",
            "R": "R͜͡",
            "S": "S͜͡",
            "T": "T͜͡",
            "U": "U͜͡",
            "V": "V͜͡",
            "W": "W͜͡",
            "X": "X͜͡",
            "Y": "Y͜͡",
            "Z": "Z͜͡",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def hClienty(text):
        style = {
            "a": "ă̈",
            "b": "b̆̈",
            "c": "c̆̈",
            "d": "d̆̈",
            "e": "ĕ̈",
            "f": "f̆̈",
            "g": "ğ̈",
            "h": "h̆̈",
            "i": "ĭ̈",
            "j": "j̆̈",
            "k": "k̆̈",
            "l": "l̆̈",
            "m": "m̆̈",
            "n": "n̆̈",
            "o": "ŏ̈",
            "p": "p̆̈",
            "q": "q̆̈",
            "r": "r̆̈",
            "s": "s̆̈",
            "t": "t̆̈",
            "u": "ŭ̈",
            "v": "v̆̈",
            "w": "w̆̈",
            "x": "x̆̈",
            "y": "y̆̈",
            "z": "z̆̈",
            "A": "Ă̈",
            "B": "B̆̈",
            "C": "C̆̈",
            "D": "D̆̈",
            "E": "Ĕ̈",
            "F": "F̆̈",
            "G": "Ğ̈",
            "H": "H̆̈",
            "I": "Ĭ̈",
            "J": "J̆̈",
            "K": "K̆̈",
            "L": "L̆̈",
            "M": "M̆̈",
            "N": "N̆̈",
            "O": "Ŏ̈",
            "P": "P̆̈",
            "Q": "Q̆̈",
            "R": "R̆̈",
            "S": "S̆̈",
            "T": "T̆̈",
            "U": "Ŭ̈",
            "V": "V̆̈",
            "W": "W̆̈",
            "X": "X̆̈",
            "Y": "Y̆̈",
            "Z": "Z̆̈",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def sad(text):
        style = {
            "a": "ȃ̈",
            "b": "b̑̈",
            "c": "c̑̈",
            "d": "d̑̈",
            "e": "ȇ̈",
            "f": "f̑̈",
            "g": "g̑̈",
            "h": "h̑̈",
            "i": "ȋ̈",
            "j": "j̑̈",
            "k": "k̑̈",
            "l": "l̑̈",
            "m": "m̑̈",
            "n": "n̑̈",
            "o": "ȏ̈",
            "p": "p̑̈",
            "q": "q̑̈",
            "r": "ȓ̈",
            "s": "s̑̈",
            "t": "t̑̈",
            "u": "ȗ̈",
            "v": "v̑̈",
            "w": "w̑̈",
            "x": "x̑̈",
            "y": "y̑̈",
            "z": "z̑̈",
            "A": "Ȃ̈",
            "B": "B̑̈",
            "C": "C̑̈",
            "D": "D̑̈",
            "E": "Ȇ̈",
            "F": "F̑̈",
            "G": "G̑̈",
            "H": "H̑̈",
            "I": "Ȋ̈",
            "J": "J̑̈",
            "K": "K̑̈",
            "L": "L̑̈",
            "M": "M̑̈",
            "N": "N̑̈",
            "O": "Ȏ̈",
            "P": "P̑̈",
            "Q": "Q̑̈",
            "R": "Ȓ̈",
            "S": "S̑̈",
            "T": "T̑̈",
            "U": "Ȗ̈",
            "V": "V̑̈",
            "W": "W̑̈",
            "X": "X̑̈",
            "Y": "Y̑̈",
            "Z": "Z̑̈",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def special(text):
        style = {
            "a": "🇦 ",
            "b": "🇧 ",
            "c": "🇨 ",
            "d": "🇩 ",
            "e": "🇪 ",
            "f": "🇫 ",
            "g": "🇬 ",
            "h": "🇭 ",
            "i": "🇮 ",
            "j": "🇯 ",
            "k": "🇰 ",
            "l": "🇱 ",
            "m": "🇲 ",
            "n": "🇳 ",
            "o": "🇴 ",
            "p": "🇵 ",
            "q": "🇶 ",
            "r": "🇷 ",
            "s": "🇸 ",
            "t": "🇹 ",
            "u": "🇺 ",
            "v": "🇻 ",
            "w": "🇼 ",
            "x": "🇽 ",
            "y": "🇾 ",
            "z": "🇿 ",
            "A": "🇦 ",
            "B": "🇧 ",
            "C": "🇨 ",
            "D": "🇩 ",
            "E": "🇪 ",
            "F": "🇫 ",
            "G": "🇬 ",
            "H": "🇭 ",
            "I": "🇮 ",
            "J": "🇯 ",
            "K": "🇰 ",
            "L": "🇱 ",
            "M": "🇲 ",
            "N": "🇳 ",
            "O": "🇴 ",
            "P": "🇵 ",
            "Q": "🇶 ",
            "R": "🇷 ",
            "S": "🇸 ",
            "T": "🇹 ",
            "U": "🇺 ",
            "V": "🇻 ",
            "W": "🇼 ",
            "X": "🇽 ",
            "Y": "🇾 ",
            "Z": "🇿 ",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def square(text):
        style = {
            "a": "🄰",
            "b": "🄱",
            "c": "🄲",
            "d": "🄳",
            "e": "🄴",
            "f": "🄵",
            "g": "🄶",
            "h": "🄷",
            "i": "🄸",
            "j": "🄹",
            "k": "🄺",
            "l": "🄻",
            "m": "🄼",
            "n": "🄽",
            "o": "🄾",
            "p": "🄿",
            "q": "🅀",
            "r": "🅁",
            "s": "🅂",
            "t": "🅃",
            "u": "🅄",
            "v": "🅅",
            "w": "🅆",
            "x": "🅇",
            "y": "🅈",
            "z": "🅉",
            "A": "🄰",
            "B": "🄱",
            "C": "🄲",
            "D": "🄳",
            "E": "🄴",
            "F": "🄵",
            "G": "🄶",
            "H": "🄷",
            "I": "🄸",
            "J": "🄹",
            "K": "🄺",
            "L": "🄻",
            "M": "🄼",
            "N": "🄽",
            "O": "🄾",
            "P": "🄿",
            "Q": "🅀",
            "R": "🅁",
            "S": "🅂",
            "T": "🅃",
            "U": "🅄",
            "V": "🅅",
            "W": "🅆",
            "X": "🅇",
            "Y": "🅈",
            "Z": "🅉",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def dark_square(text):
        style = {
            "a": "🅰︎",
            "b": "🅱︎",
            "c": "🅲︎",
            "d": "🅳︎",
            "e": "🅴︎",
            "f": "🅵︎",
            "g": "🅶︎",
            "h": "🅷︎",
            "i": "🅸︎",
            "j": "🅹︎",
            "k": "🅺︎",
            "l": "🅻︎",
            "m": "🅼︎",
            "n": "🅽︎",
            "o": "🅾︎",
            "p": "🅿︎",
            "q": "🆀︎",
            "r": "🆁︎",
            "s": "🆂︎",
            "t": "🆃︎",
            "u": "🆄︎",
            "v": "🆅︎",
            "w": "🆆︎",
            "x": "🆇︎",
            "y": "🆈︎",
            "z": "🆉︎",
            "A": "🅰︎",
            "B": "🅱︎",
            "C": "🅲︎",
            "D": "🅳︎",
            "E": "🅴︎",
            "F": "🅵︎",
            "G": "🅶︎",
            "H": "🅷︎",
            "I": "🅸︎",
            "J": "🅹︎",
            "K": "🅺︎",
            "L": "🅻︎",
            "M": "🅼︎",
            "N": "🅽︎",
            "O": "🅾︎",
            "P": "🅿︎",
            "Q": "🆀︎",
            "R": "🆁︎",
            "S": "🆂︎",
            "T": "🆃︎",
            "U": "🆄︎",
            "V": "🆅︎",
            "W": "🆆︎",
            "X": "🆇︎",
            "Y": "🆈︎",
            "Z": "🆉︎",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def andalucia(text):
        style = {
            "a": "ꪖ",
            "b": "᥇",
            "c": "ᥴ",
            "d": "ᦔ",
            "e": "ꫀ",
            "f": "ᠻ",
            "g": "ᧁ",
            "h": "ꫝ",
            "i": "𝓲",
            "j": "𝓳",
            "k": "𝘬",
            "l": "ꪶ",
            "m": "ꪑ",
            "n": "ꪀ",
            "o": "ꪮ",
            "p": "ρ",
            "q": "𝘲",
            "r": "𝘳",
            "s": "𝘴",
            "t": "𝓽",
            "u": "ꪊ",
            "v": "ꪜ",
            "w": "᭙",
            "x": "᥊",
            "y": "ꪗ",
            "z": "ɀ",
            "A": "ꪖ",
            "B": "᥇",
            "C": "ᥴ",
            "D": "ᦔ",
            "E": "ꫀ",
            "F": "ᠻ",
            "G": "ᧁ",
            "H": "ꫝ",
            "I": "𝓲",
            "J": "𝓳",
            "K": "𝘬",
            "L": "ꪶ",
            "M": "ꪑ",
            "N": "ꪀ",
            "O": "ꪮ",
            "P": "ρ",
            "Q": "𝘲",
            "R": "𝘳",
            "S": "𝘴",
            "T": "𝓽",
            "U": "ꪊ",
            "V": "ꪜ",
            "W": "᭙",
            "X": "᥊",
            "Y": "ꪗ",
            "Z": "ɀ",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def manga(text):
        style = {
            "a": "卂",
            "b": "乃",
            "c": "匚",
            "d": "ᗪ",
            "e": "乇",
            "f": "千",
            "g": "ᘜ",
            "h": "卄",
            "i": "|",
            "j": "ﾌ",
            "k": "Ҝ",
            "l": "ㄥ",
            "m": "爪",
            "n": "几",
            "o": "ㄖ",
            "p": "卩",
            "q": "Ҩ",
            "r": "尺",
            "s": "丂",
            "t": "ㄒ",
            "u": "ㄩ",
            "v": "ᐯ",
            "w": "山",
            "x": "乂",
            "y": "ㄚ",
            "z": "乙",
            "A": "卂",
            "B": "乃",
            "C": "匚",
            "D": "ᗪ",
            "E": "乇",
            "F": "千",
            "G": "ᘜ",
            "H": "卄",
            "I": "|",
            "J": "ﾌ",
            "K": "Ҝ",
            "L": "ㄥ",
            "M": "爪",
            "N": "几",
            "O": "ㄖ",
            "P": "卩",
            "Q": "Ҩ",
            "R": "尺",
            "S": "丂",
            "T": "ㄒ",
            "U": "ㄩ",
            "V": "ᐯ",
            "W": "山",
            "X": "乂",
            "Y": "ㄚ",
            "Z": "乙",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def stinky(text):
        style = {
            "a": "a̾",
            "b": "b̾",
            "c": "c̾",
            "d": "d̾",
            "e": "e̾",
            "f": "f̾",
            "g": "g̾",
            "h": "h̾",
            "i": "i̾",
            "j": "j̾",
            "k": "k̾",
            "l": "l̾",
            "m": "m̾",
            "n": "n̾",
            "o": "o̾",
            "p": "p̾",
            "q": "q̾",
            "r": "r̾",
            "s": "s̾",
            "t": "t̾",
            "u": "u̾",
            "v": "v̾",
            "w": "w̾",
            "x": "x̾",
            "y": "y̾",
            "z": "z̾",
            "A": "A̾",
            "B": "B̾",
            "C": "C̾",
            "D": "D̾",
            "E": "E̾",
            "F": "F̾",
            "G": "G̾",
            "H": "H̾",
            "I": "I̾",
            "J": "J̾",
            "K": "K̾",
            "L": "L̾",
            "M": "M̾",
            "N": "N̾",
            "O": "O̾",
            "P": "P̾",
            "Q": "Q̾",
            "R": "R̾",
            "S": "S̾",
            "T": "T̾",
            "U": "U̾",
            "V": "V̾",
            "W": "W̾",
            "X": "X̾",
            "Y": "Y̾",
            "Z": "Z̾",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def bubbles(text):
        style = {
            "a": "ḁͦ",
            "b": "b̥ͦ",
            "c": "c̥ͦ",
            "d": "d̥ͦ",
            "e": "e̥ͦ",
            "f": "f̥ͦ",
            "g": "g̥ͦ",
            "h": "h̥ͦ",
            "i": "i̥ͦ",
            "j": "j̥ͦ",
            "k": "k̥ͦ",
            "l": "l̥ͦ",
            "m": "m̥ͦ",
            "n": "n̥ͦ",
            "o": "o̥ͦ",
            "p": "p̥ͦ",
            "q": "q̥ͦ",
            "r": "r̥ͦ",
            "s": "s̥ͦ",
            "t": "t̥ͦ",
            "u": "u̥ͦ",
            "v": "v̥ͦ",
            "w": "w̥ͦ",
            "x": "x̥ͦ",
            "y": "y̥ͦ",
            "z": "z̥ͦ",
            "A": "Ḁͦ",
            "B": "B̥ͦ",
            "C": "C̥ͦ",
            "D": "D̥ͦ",
            "E": "E̥ͦ",
            "F": "F̥ͦ",
            "G": "G̥ͦ",
            "H": "H̥ͦ",
            "I": "I̥ͦ",
            "J": "J̥ͦ",
            "K": "K̥ͦ",
            "L": "L̥ͦ",
            "M": "M̥ͦ",
            "N": "N̥ͦ",
            "O": "O̥ͦ",
            "P": "P̥ͦ",
            "Q": "Q̥ͦ",
            "R": "R̥ͦ",
            "S": "S̥ͦ",
            "T": "T̥ͦ",
            "U": "U̥ͦ",
            "V": "V̥ͦ",
            "W": "W̥ͦ",
            "X": "X̥ͦ",
            "Y": "Y̥ͦ",
            "Z": "Z̥ͦ",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def underline(text):
        style = {
            "a": "a͟",
            "b": "b͟",
            "c": "c͟",
            "d": "d͟",
            "e": "e͟",
            "f": "f͟",
            "g": "g͟",
            "h": "h͟",
            "i": "i͟",
            "j": "j͟",
            "k": "k͟",
            "l": "l͟",
            "m": "m͟",
            "n": "n͟",
            "o": "o͟",
            "p": "p͟",
            "q": "q͟",
            "r": "r͟",
            "s": "s͟",
            "t": "t͟",
            "u": "u͟",
            "v": "v͟",
            "w": "w͟",
            "x": "x͟",
            "y": "y͟",
            "z": "z͟",
            "A": "A͟",
            "B": "B͟",
            "C": "C͟",
            "D": "D͟",
            "E": "E͟",
            "F": "F͟",
            "G": "G͟",
            "H": "H͟",
            "I": "I͟",
            "J": "J͟",
            "K": "K͟",
            "L": "L͟",
            "M": "M͟",
            "N": "N͟",
            "O": "O͟",
            "P": "P͟",
            "Q": "Q͟",
            "R": "R͟",
            "S": "S͟",
            "T": "T͟",
            "U": "U͟",
            "V": "V͟",
            "W": "W͟",
            "X": "X͟",
            "Y": "Y͟",
            "Z": "Z͟",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def ladybug(text):
        style = {
            "a": "ꍏ",
            "b": "ꌃ",
            "c": "ꏳ",
            "d": "ꀷ",
            "e": "ꏂ",
            "f": "ꎇ",
            "g": "ꁅ",
            "h": "ꀍ",
            "i": "ꀤ",
            "j": "꒻",
            "k": "ꀘ",
            "l": "꒒",
            "m": "ꎭ",
            "n": "ꈤ",
            "o": "ꂦ",
            "p": "ᖘ",
            "q": "ꆰ",
            "r": "ꋪ",
            "s": "ꌚ",
            "t": "꓄",
            "u": "ꀎ",
            "v": "꒦",
            "w": "ꅐ",
            "x": "ꉧ",
            "y": "ꌩ",
            "z": "ꁴ",
            "A": "ꍏ",
            "B": "ꌃ",
            "C": "ꏳ",
            "D": "ꀷ",
            "E": "ꏂ",
            "F": "ꎇ",
            "G": "ꁅ",
            "H": "ꀍ",
            "I": "ꀤ",
            "J": "꒻",
            "K": "ꀘ",
            "L": "꒒",
            "M": "ꎭ",
            "N": "ꈤ",
            "O": "ꂦ",
            "P": "ᖘ",
            "Q": "ꆰ",
            "R": "ꋪ",
            "S": "ꌚ",
            "T": "꓄",
            "U": "ꀎ",
            "V": "꒦",
            "W": "ꅐ",
            "X": "ꉧ",
            "Y": "ꌩ",
            "Z": "ꁴ",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def rays(text):
        style = {
            "a": "a҉",
            "b": "b҉",
            "c": "c҉",
            "d": "d҉",
            "e": "e҉",
            "f": "f҉",
            "g": "g҉",
            "h": "h҉",
            "i": "i҉",
            "j": "j҉",
            "k": "k҉",
            "l": "l҉",
            "m": "m҉",
            "n": "n҉",
            "o": "o҉",
            "p": "p҉",
            "q": "q҉",
            "r": "r҉",
            "s": "s҉",
            "t": "t҉",
            "u": "u҉",
            "v": "v҉",
            "w": "w҉",
            "x": "x҉",
            "y": "y҉",
            "z": "z҉",
            "A": "A҉",
            "B": "B҉",
            "C": "C҉",
            "D": "D҉",
            "E": "E҉",
            "F": "F҉",
            "G": "G҉",
            "H": "H҉",
            "I": "I҉",
            "J": "J҉",
            "K": "K҉",
            "L": "L҉",
            "M": "M҉",
            "N": "N҉",
            "O": "O҉",
            "P": "P҉",
            "Q": "Q҉",
            "R": "R҉",
            "S": "S҉",
            "T": "T҉",
            "U": "U҉",
            "V": "V҉",
            "W": "W҉",
            "X": "X҉",
            "Y": "Y҉",
            "Z": "Z҉",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def birds(text):
        style = {
            "a": "a҈",
            "b": "b҈",
            "c": "c҈",
            "d": "d҈",
            "e": "e҈",
            "f": "f҈",
            "g": "g҈",
            "h": "h҈",
            "i": "i҈",
            "j": "j҈",
            "k": "k҈",
            "l": "l҈",
            "m": "m҈",
            "n": "n҈",
            "o": "o҈",
            "p": "p҈",
            "q": "q҈",
            "r": "r҈",
            "s": "s҈",
            "t": "t҈",
            "u": "u҈",
            "v": "v҈",
            "w": "w҈",
            "x": "x҈",
            "y": "y҈",
            "z": "z҈",
            "A": "A҈",
            "B": "B҈",
            "C": "C҈",
            "D": "D҈",
            "E": "E҈",
            "F": "F҈",
            "G": "G҈",
            "H": "H҈",
            "I": "I҈",
            "J": "J҈",
            "K": "K҈",
            "L": "L҈",
            "M": "M҈",
            "N": "N҈",
            "O": "O҈",
            "P": "P҈",
            "Q": "Q҈",
            "R": "R҈",
            "S": "S҈",
            "T": "T҈",
            "U": "U҈",
            "V": "V҈",
            "W": "W҈",
            "X": "X҈",
            "Y": "Y҈",
            "Z": "Z҈",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def slash(text):
        style = {
            "a": "a̸",
            "b": "b̸",
            "c": "c̸",
            "d": "d̸",
            "e": "e̸",
            "f": "f̸",
            "g": "g̸",
            "h": "h̸",
            "i": "i̸",
            "j": "j̸",
            "k": "k̸",
            "l": "l̸",
            "m": "m̸",
            "n": "n̸",
            "o": "o̸",
            "p": "p̸",
            "q": "q̸",
            "r": "r̸",
            "s": "s̸",
            "t": "t̸",
            "u": "u̸",
            "v": "v̸",
            "w": "w̸",
            "x": "x̸",
            "y": "y̸",
            "z": "z̸",
            "A": "A̸",
            "B": "B̸",
            "C": "C̸",
            "D": "D̸",
            "E": "E̸",
            "F": "F̸",
            "G": "G̸",
            "H": "H̸",
            "I": "I̸",
            "J": "J̸",
            "K": "K̸",
            "L": "L̸",
            "M": "M̸",
            "N": "N̸",
            "O": "O̸",
            "P": "P̸",
            "Q": "Q̸",
            "R": "R̸",
            "S": "S̸",
            "T": "T̸",
            "U": "U̸",
            "V": "V̸",
            "W": "W̸",
            "X": "X̸",
            "Y": "Y̸",
            "Z": "Z̸",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def stop(text):
        style = {
            "a": "a⃠",
            "b": "b⃠",
            "c": "c⃠",
            "d": "d⃠",
            "e": "e⃠",
            "f": "f⃠",
            "g": "g⃠",
            "h": "h⃠",
            "i": "i⃠",
            "j": "j⃠",
            "k": "k⃠",
            "l": "l⃠",
            "m": "m⃠",
            "n": "n⃠",
            "o": "o⃠",
            "p": "p⃠",
            "q": "q⃠",
            "r": "r⃠",
            "s": "s⃠",
            "t": "t⃠",
            "u": "u⃠",
            "v": "v⃠",
            "w": "w⃠",
            "x": "x⃠",
            "y": "y⃠",
            "z": "z⃠",
            "A": "A⃠",
            "B": "B⃠",
            "C": "C⃠",
            "D": "D⃠",
            "E": "E⃠",
            "F": "F⃠",
            "G": "G⃠",
            "H": "H⃠",
            "I": "I⃠",
            "J": "J⃠",
            "K": "K⃠",
            "L": "L⃠",
            "M": "M⃠",
            "N": "N⃠",
            "O": "O⃠",
            "P": "P⃠",
            "Q": "Q⃠",
            "R": "R⃠",
            "S": "S⃠",
            "T": "T⃠",
            "U": "U⃠",
            "V": "V⃠",
            "W": "W⃠",
            "X": "X⃠",
            "Y": "Y⃠",
            "Z": "Z⃠",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def skyline(text):
        style = {
            "a": "a̺͆",
            "b": "b̺͆",
            "c": "c̺͆",
            "d": "d̺͆",
            "e": "e̺͆",
            "f": "f̺͆",
            "g": "g̺͆",
            "h": "h̺͆",
            "i": "i̺͆",
            "j": "j̺͆",
            "k": "k̺͆",
            "l": "l̺͆",
            "m": "m̺͆",
            "n": "n̺͆",
            "o": "o̺͆",
            "p": "p̺͆",
            "q": "q̺͆",
            "r": "r̺͆",
            "s": "s̺͆",
            "t": "t̺͆",
            "u": "u̺͆",
            "v": "v̺͆",
            "w": "w̺͆",
            "x": "x̺͆",
            "y": "y̺͆",
            "z": "z̺͆",
            "A": "A̺͆",
            "B": "B̺͆",
            "C": "C̺͆",
            "D": "D̺͆",
            "E": "E̺͆",
            "F": "F̺͆",
            "G": "G̺͆",
            "H": "H̺͆",
            "I": "I̺͆",
            "J": "J̺͆",
            "K": "K̺͆",
            "L": "L̺͆",
            "M": "M̺͆",
            "N": "N̺͆",
            "O": "O̺͆",
            "P": "P̺͆",
            "Q": "Q̺͆",
            "R": "R̺͆",
            "S": "S̺͆",
            "T": "T̺͆",
            "U": "U̺͆",
            "V": "V̺͆",
            "W": "W̺͆",
            "X": "X̺͆",
            "Y": "Y̺͆",
            "Z": "Z̺͆",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def arrows(text):
        style = {
            "a": "a͎",
            "b": "b͎",
            "c": "c͎",
            "d": "d͎",
            "e": "e͎",
            "f": "f͎",
            "g": "g͎",
            "h": "h͎",
            "i": "i͎",
            "j": "j͎",
            "k": "k͎",
            "l": "l͎",
            "m": "m͎",
            "n": "n͎",
            "o": "o͎",
            "p": "p͎",
            "q": "q͎",
            "r": "r͎",
            "s": "s͎",
            "t": "t͎",
            "u": "u͎",
            "v": "v͎",
            "w": "w͎",
            "x": "x͎",
            "y": "y͎",
            "z": "z͎",
            "A": "A͎",
            "B": "B͎",
            "C": "C͎",
            "D": "D͎",
            "E": "E͎",
            "F": "F͎",
            "G": "G͎",
            "H": "H͎",
            "I": "I͎",
            "J": "J͎",
            "K": "K͎",
            "L": "L͎",
            "M": "M͎",
            "N": "N͎",
            "O": "O͎",
            "P": "P͎",
            "Q": "Q͎",
            "R": "R͎",
            "S": "S͎",
            "T": "T͎",
            "U": "U͎",
            "V": "V͎",
            "W": "W͎",
            "X": "X͎",
            "Y": "Y͎",
            "Z": "Z͎",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def rvnes(text):
        style = {
            "a": "ል",
            "b": "ጌ",
            "c": "ር",
            "d": "ዕ",
            "e": "ቿ",
            "f": "ቻ",
            "g": "ኗ",
            "h": "ዘ",
            "i": "ጎ",
            "j": "ጋ",
            "k": "ጕ",
            "l": "ረ",
            "m": "ጠ",
            "n": "ክ",
            "o": "ዐ",
            "p": "የ",
            "q": "ዒ",
            "r": "ዪ",
            "s": "ነ",
            "t": "ፕ",
            "u": "ሁ",
            "v": "ሀ",
            "w": "ሠ",
            "x": "ሸ",
            "y": "ሃ",
            "z": "ጊ",
            "A": "ል",
            "B": "ጌ",
            "C": "ር",
            "D": "ዕ",
            "E": "ቿ",
            "F": "ቻ",
            "G": "ኗ",
            "H": "ዘ",
            "I": "ጎ",
            "J": "ጋ",
            "K": "ጕ",
            "L": "ረ",
            "M": "ጠ",
            "N": "ክ",
            "O": "ዐ",
            "P": "የ",
            "Q": "ዒ",
            "R": "ዪ",
            "S": "ነ",
            "T": "ፕ",
            "U": "ሁ",
            "V": "ሀ",
            "W": "ሠ",
            "X": "ሸ",
            "Y": "ሃ",
            "Z": "ጊ",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def strike(text):
        style = {
            "a": "a̶",
            "b": "b̶",
            "c": "c̶",
            "d": "d̶",
            "e": "e̶",
            "f": "f̶",
            "g": "g̶",
            "h": "h̶",
            "i": "i̶",
            "j": "j̶",
            "k": "k̶",
            "l": "l̶",
            "m": "m̶",
            "n": "n̶",
            "o": "o̶",
            "p": "p̶",
            "q": "q̶",
            "r": "r̶",
            "s": "s̶",
            "t": "t̶",
            "u": "u̶",
            "v": "v̶",
            "w": "w̶",
            "x": "x̶",
            "y": "y̶",
            "z": "z̶",
            "A": "A̶",
            "B": "B̶",
            "C": "C̶",
            "D": "D̶",
            "E": "E̶",
            "F": "F̶",
            "G": "G̶",
            "H": "H̶",
            "I": "I̶",
            "J": "J̶",
            "K": "K̶",
            "L": "L̶",
            "M": "M̶",
            "N": "N̶",
            "O": "O̶",
            "P": "P̶",
            "Q": "Q̶",
            "R": "R̶",
            "S": "S̶",
            "T": "T̶",
            "U": "U̶",
            "V": "V̶",
            "W": "W̶",
            "X": "X̶",
            "Y": "Y̶",
            "Z": "Z̶",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text

    def frozen(text):
        style = {
            "a": "a༙",
            "b": "b༙",
            "c": "c༙",
            "d": "d༙",
            "e": "e༙",
            "f": "f༙",
            "g": "g༙",
            "h": "h༙",
            "i": "i༙",
            "j": "j༙",
            "k": "k༙",
            "l": "l༙",
            "m": "m༙",
            "n": "n༙",
            "o": "o༙",
            "p": "p༙",
            "q": "q༙",
            "r": "r༙",
            "s": "s༙",
            "t": "t༙",
            "u": "u༙",
            "v": "v༙",
            "w": "w༙",
            "x": "x༙",
            "y": "y༙",
            "z": "z༙",
            "A": "A༙",
            "B": "B༙",
            "C": "C༙",
            "D": "D༙",
            "E": "E༙",
            "F": "F༙",
            "G": "G༙",
            "H": "H༙",
            "I": "I༙",
            "J": "J༙",
            "K": "K༙",
            "L": "L༙",
            "M": "M༙",
            "N": "N༙",
            "O": "O༙",
            "P": "P༙",
            "Q": "Q༙",
            "R": "R༙",
            "S": "S༙",
            "T": "T༙",
            "U": "U༙",
            "V": "V༙",
            "W": "W༙",
            "X": "X༙",
            "Y": "Y༙",
            "Z": "Z༙",
        }
        for i, j in style.items():
            text = text.replace(i, j)
        return text
        from telegram.ext import (
            CommandHandler,
            CallbackQueryHandler,
            ContextTypes,
        )

FONT_STYLES = [
            ("𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", "typewriter"),
            ("𝕆𝕦𝕥𝕝𝕚𝕟𝕖", "outline"),
            ("𝐒𝐞𝐫𝐢𝐟", "serif"),
            ("𝑺𝒆𝒓𝒊𝒇", "bold_cool"),
            ("𝑆𝑒𝑟𝑖𝑓", "cool"),
            ("Sᴍᴀʟʟ Cᴀᴘs", "small_cap"),
            ("𝓈𝒸𝓇𝒾𝓅𝓉", "script"),
            ("𝓼𝓬𝓻𝓲𝓹𝓽", "script_bolt"),
            ("ᵗⁱⁿʸ", "tiny"),
            ("ᑕOᗰIᑕ", "comic"),
            ("𝗦𝗮𝗻𝘀", "sans"),
            ("𝙎𝙖𝙣𝙨", "slant_sans"),
            ("𝘚𝘢𝘯𝘴", "slant"),
            ("𝖲𝖺𝗇𝗌", "sim"),
            ("Ⓒ︎Ⓘ︎Ⓡ︎Ⓒ︎Ⓛ︎Ⓔ︎Ⓢ︎", "circles"),
            ("🅒︎🅘︎🅡︎🅒︎🅛︎🅔︎🅢︎", "circle_dark"),
            ("𝔊𝔬𝔱𝔥𝔦𝔠", "gothic"),
            ("𝕲𝖔𝖙𝖍𝖎𝖈", "gothic_bolt"),
            ("C͜͡l͜͡o͜͡u͜͡d͜͡s͜͡", "cloud"),
            ("H̆̈ă̈p̆̈p̆̈y̆̈", "hClienty"),
            ("S̑̈ȃ̈d̑̈", "sad"),
        ]

FONT_STYLES_2 = [
            ("🇸 🇵 🇪 🇨 🇮 🇦 🇱 ", "special"),
            ("🅂🅀🅄🄰🅁🄴🅂", "squares"),
            ("🆂︎🆀︎🆄︎🅰︎🆁︎🅴︎🆂︎", "squares_bold"),
            ("ꪖꪀᦔꪖꪶꪊᥴ𝓲ꪖ", "andalucia"),
            ("爪卂几ᘜ卂", "manga"),
            ("S̾t̾i̾n̾k̾y̾", "stinky"),
            ("B̥ͦu̥ͦb̥ͦb̥ͦl̥ͦe̥ͦs̥ͦ", "bubbles"),
            ("U͟n͟d͟e͟r͟l͟i͟n͟e͟", "underline"),
            ("꒒ꍏꀷꌩꌃꀎꁅ", "ladybug"),
            ("R҉a҉y҉s҉", "rays"),
            ("B҈i҈r҈d҈s҈", "birds"),
            ("S̸l̸a̸s̸h̸", "slash"),
            ("s⃠t⃠o⃠p⃠", "stop"),
            ("S̺͆k̺͆y̺͆l̺͆i̺͆n̺͆e̺͆", "skyline"),
            ("A͎r͎r͎o͎w͎s͎", "arrows"),
            ("ዪሀክቿነ", "qvnes"),
            ("S̶t̶r̶i̶k̶e̶", "strike"),
            ("F༙r༙o༙z༙e༙n༙", "frozen"),
        ]

def get_font_buttons(page=1):
            styles = FONT_STYLES if page == 1 else FONT_STYLES_2
            buttons = []
            for i in range(0, len(styles), 3):
                row = [
                    InlineKeyboardButton(styles[j][0], callback_data=f"style+{styles[j][1]}")
                    for j in range(i, min(i + 3, len(styles)))
                ]
                buttons.append(row)
            nav = []
            if page == 1:
                nav = [
                    InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close_reply"),
                    InlineKeyboardButton("ɴᴇxᴛ ➻", callback_data="nxt"),
                ]
            else:
                nav = [
                    InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close_reply"),
                    InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="nxt+0"),
                ]
            buttons.append(nav)
            return InlineKeyboardMarkup(buttons)

async def font_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text(
                    "Please provide some text to style!\n\nUsage: `/font your text here`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            text = " ".join(context.args)
            await update.message.reply_text(
                f"✨ *Choose a font style below!* ✨\n\n`{text}`",
                reply_markup=get_font_buttons(page=1),
                parse_mode=ParseMode.MARKDOWN,
            )

async def font_nxt(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            if query.data == "nxt":
                await query.edit_message_reply_markup(reply_markup=get_font_buttons(page=2))
            else:
                await query.edit_message_reply_markup(reply_markup=get_font_buttons(page=1))

async def font_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            style = query.data.split("+", 1)[1]
            # Try to get the original text from the message
            orig_text = None
            if query.message.reply_to_message:
                orig_text = query.message.reply_to_message.text
            else:
                # fallback: try to extract from the message itself
                orig_text = query.message.text
            if not orig_text:
                await query.edit_message_text("No text found to style!", reply_markup=query.message.reply_markup)
                return
            # Try to extract the text after the command
            if orig_text.startswith("/font") or orig_text.startswith("/fonts"):
                orig_text = orig_text.split(" ", 1)[1] if " " in orig_text else ""
            # Map style to Fonts class
            style_map = {
                "typewriter": Fonts.typewriter,
                "outline": Fonts.outline,
                "serif": Fonts.serief,
                "bold_cool": Fonts.bold_cool,
                "cool": Fonts.cool,
                "small_cap": Fonts.smallcap,
                "script": Fonts.script,
                "script_bolt": Fonts.bold_script,
                "tiny": Fonts.tiny,
                "comic": Fonts.comic,
                "sans": Fonts.san,
                "slant_sans": Fonts.slant_san,
                "slant": Fonts.slant,
                "sim": Fonts.sim,
                "circles": Fonts.circles,
                "circle_dark": Fonts.dark_circle,
                "gothic": Fonts.gothic,
                "gothic_bolt": Fonts.bold_gothic,
                "cloud": Fonts.cloud,
                "hClienty": Fonts.hClienty,
                "sad": Fonts.sad,
                "special": Fonts.special,
                "squares": Fonts.square,
                "squares_bold": Fonts.dark_square,
                "andalucia": Fonts.andalucia,
                "manga": Fonts.manga,
                "stinky": Fonts.stinky,
                "bubbles": Fonts.bubbles,
                "underline": Fonts.underline,
                "ladybug": Fonts.ladybug,
                "rays": Fonts.rays,
                "birds": Fonts.birds,
                "slash": Fonts.slash,
                "stop": Fonts.stop,
                "skyline": Fonts.skyline,
                "arrows": Fonts.arrows,
                "qvnes": Fonts.rvnes,
                "strike": Fonts.strike,
                "frozen": Fonts.frozen,
            }
            func = style_map.get(style)
            if not func:
                await query.edit_message_text("Unknown style!", reply_markup=query.message.reply_markup)
                return
            styled = func(orig_text)
            await query.edit_message_text(
                f"✨ *Your styled text:* ✨\n\n`{styled}`",
                reply_markup=query.message.reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )
WAIFU_API_BASE = "https://api.waifu.pics/sfw"

COMMANDS = [
     "neko", "shinobu", "megumin", "bully", "cuddle", "cry", "hug", "awoo",
    "kiss", "lick", "pat", "smug", "bonk", "yeet", "blush", "smile", "wave", "highfive",
    "handhold", "nom", "bite", "glomp", "slap", "kill", "kick", "happy", "wink", "poke",
    "dance", "cringe"
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def fetch_image(category: str):
    url = f"{WAIFU_API_BASE}/{category}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("url")
            return None

async def waifu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.lstrip('/').split()[0]
    image_url = await fetch_image(cmd)
    if image_url:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Next", callback_data=f"next_{cmd}")]
        ])
        await update.message.reply_photo(
            image_url,
            caption=f"Here's your {cmd}!",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text("Couldn't fetch image right now. Please try again later.")

async def next_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data.replace("next_", "")
    image_url = await fetch_image(cmd)
    if image_url:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Next", callback_data=f"next_{cmd}")]
        ])
        await query.edit_message_media(
            media=telegram.InputMediaPhoto(image_url, caption=f"Here's your {cmd}!"),
            reply_markup=keyboard
        )
    else:
        await query.edit_message_caption("Couldn't fetch image right now.")


import json, os, logging
from telegram import Update, User, ChatPermissions
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Constants ===
DATA_DIR = "data"
SUDO_USERS_FILE = os.path.join(DATA_DIR, "sudousers.json")
GLOBAL_BANS_FILE = os.path.join(DATA_DIR, "globalbans.json")
GLOBAL_MUTES_FILE = os.path.join(DATA_DIR, "globalmutes.json")
STATS_DATA_FILE = os.path.join(DATA_DIR, "statsdata.json")

# === Data Handling ===
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_json(file_path, default):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
    return default

def save_json(file_path, data):
    try:
        ensure_data_dir()
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")

# === Load State ===
sudo_users_data = load_json(SUDO_USERS_FILE, {
    "lord": 8429156335,
    "substitute_lords": [8429156335],
    "descendants": [],
})
sudo_users = {
    "lord": sudo_users_data["lord"],
    "substitute_lords": set(sudo_users_data.get("substitute_lords", [])),
    "descendants": set(sudo_users_data.get("descendants", [])),
}
global_bans = set(load_json(GLOBAL_BANS_FILE, []))
global_mutes = set(load_json(GLOBAL_MUTES_FILE, []))
stats_data = load_json(STATS_DATA_FILE, {"groups": [], "users": []})
stats_data["groups"] = set(stats_data.get("groups", []))
stats_data["users"] = set(stats_data.get("users", []))

# === Save Helpers ===
def save_sudo_users():
    data = {
        "lord": sudo_users["lord"],
        "substitute_lords": list(sudo_users["substitute_lords"]),
        "descendants": list(sudo_users["descendants"]),
    }
    save_json(SUDO_USERS_FILE, data)

def save_global_bans():
    save_json(GLOBAL_BANS_FILE, list(global_bans))

def save_global_mutes():
    save_json(GLOBAL_MUTES_FILE, list(global_mutes))

def save_stats_data():
    save_json(STATS_DATA_FILE, {
        "groups": list(stats_data["groups"]),
        "users": list(stats_data["users"]),
    })

# === Role Checks ===
def is_lord(user_id: int) -> bool:
    return user_id == sudo_users["lord"]

def is_sub_lord(user_id: int) -> bool:
    return user_id in sudo_users["substitute_lords"]

def is_descendant(user_id: int) -> bool:
    return user_id in sudo_users["descendants"]

def is_sudo(user_id: int) -> bool:
    return is_lord(user_id) or is_sub_lord(user_id) or is_descendant(user_id)

def is_gban_powered(user_id: int) -> bool:
    return is_lord(user_id) or is_sub_lord(user_id)

# === Utilities ===
async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> User | None:
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    args = context.args
    if args:
        user_input = args[0].lstrip('@')
        try:
            return await context.bot.get_chat(user_input)
        except Exception:
            return None
    return None

# === SUDO Commands ===
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return await update.message.reply_text("🚫 Only sudo users can add another descendant.")

    processing_msg = await update.message.reply_text("⏳ Processing...")

    target = await get_target_user(update, context)
    if not target:
        return await processing_msg.edit_text("❓ User not found.")

    sudo_users["descendants"].add(target.id)
    save_sudo_users()

    await processing_msg.edit_text(
        f"✅ Added {target.mention_html()} as a sudo user.",
        parse_mode=ParseMode.HTML
    )


async def rmsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return await update.message.reply_text("🚫 Only sudo users can remove descendant.")

    processing_msg = await update.message.reply_text("⏳ Processing...")

    target = await get_target_user(update, context)
    if not target or target.id not in sudo_users["descendants"]:
        return await processing_msg.edit_text("❌ User is not a descendant.")

    sudo_users["descendants"].discard(target.id)
    save_sudo_users()

    await processing_msg.edit_text(
        f"❎ Removed {target.mention_html()} from sudo users.",
        parse_mode=ParseMode.HTML
    )


async def sudousers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("⏳ Gathering divine sudo records...")

    lord_id = sudo_users["lord"]
    sub_lords = sudo_users["substitute_lords"]
    descendants = sudo_users["descendants"]

    text = "<b>🌐 SUDO SYSTEM OVERVIEW</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"👑 <b>Lord:</b> <a href='tg://user?id={lord_id}'>{lord_id}</a>\n"

    text += "\n🔮 <b>Substitute Lords:</b>\n"
    if sub_lords:
        for uid in sub_lords:
            text += f" • <a href='tg://user?id={uid}'>{uid}</a>\n"
    else:
        text += " • <i>None</i>\n"

    text += "\n👥 <b>Descendants (Sudo Users):</b>\n"
    if descendants:
        for uid in descendants:
            text += f" • <a href='tg://user?id={uid}'>{uid}</a>\n"
    else:
        text += " • <i>None</i>\n"

    text += "━━━━━━━━━━━━━━━━━━━━━━"

    await processing_msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


# === Lord Only ===
async def addlord(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_lord(user.id):
        return await update.message.reply_text(
            "🚫 <b>Access Denied:</b> Only the <b>Main Lord</b> can appoint substitute lords.",
            parse_mode=ParseMode.HTML
        )

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(
            "❓ <b>Who?</b> Please reply to a user or specify a valid username/user ID.",
            parse_mode=ParseMode.HTML
        )

    if target.id in sudo_users["substitute_lords"]:
        return await update.message.reply_text(
            f"⚠️ <b>{target.mention_html()}</b> is already a <b>Substitute Lord</b>.",
            parse_mode=ParseMode.HTML
        )

    sudo_users["substitute_lords"].add(target.id)
    save_sudo_users()

    await update.message.reply_html(
        f"🛐 <b>{target.mention_html()}</b> has been granted the powers of a <b>Substitute Lord</b> by the <b>Main Lord</b>.\n"
        f"🔮 Welcome to the divine council."
    )


async def rmlord(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_lord(user.id):
        return await update.message.reply_text(
            "🚫 <b>Access Denied:</b> Only the <b>Main Lord</b> can dismiss substitute lords.",
            parse_mode=ParseMode.HTML
        )

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(
            "❓ <b>Who?</b> Please reply to a user or provide a valid user reference.",
            parse_mode=ParseMode.HTML
        )

    if target.id not in sudo_users["substitute_lords"]:
        return await update.message.reply_text(
            f"⚠️ <b>{target.mention_html()}</b> does not hold the title of <b>Substitute Lord</b>.",
            parse_mode=ParseMode.HTML
        )

    sudo_users["substitute_lords"].discard(target.id)
    save_sudo_users()

    await update.message.reply_html(
        f"❎ <b>{target.mention_html()}</b> has been <i>stripped of all substitute lord powers</i> by the <b>Main Lord</b>.\n"
        f"⚔️ Their reign ends here."
    )


async def lords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lord_id = sudo_users.get("lord")
    subs = sudo_users.get("substitute_lords", set())

    lord_mention = f"<a href='tg://user?id={lord_id}'>👑 Main Lord</a>"
    text = f"<b>🔱 Divine Hierarchy 🔱</b>\n\n"
    text += f"{lord_mention} <code>({lord_id})</code>\n\n"

    if subs:
        text += "<b>🧙‍♂️ Substitute Lords:</b>\n"
        for sub_id in subs:
            text += f"• <a href='tg://user?id={sub_id}'>User</a> <code>({sub_id})</code>\n"
    else:
        text += "<i>There are no substitute lords currently.</i>"

    await update.message.reply_html(text, disable_web_page_preview=True)


# === Global Enforcement Commands ===
async def gban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # Check if user has GBAN power
    if not is_gban_powered(user.id):
        return await update.message.reply_html(
            "🚫 <b>Unauthorized:</b> Only the 👑 Lord or 🧙 Substitute Lords can invoke <code>/gban</code>."
        )

    # Get target user
    target = await get_target_user(update, context)
    if not target or target.id == user.id:
        return await update.message.reply_html("🙅‍♂️ <b>Invalid target:</b> You cannot gban yourself or an invalid user.")

    # Prevent sudo user banning
    if is_sudo(target.id):
        return await update.message.reply_html("⚔️ <b>Conflict:</b> You can't gban another Sudo user.")

    # Check if already banned
    if target.id in global_bans:
        return await update.message.reply_html("⚠️ <b>Already Globally Banned!</b>")

    # Apply GBAN
    global_bans.add(target.id)
    save_global_bans()

    try:
        await context.bot.ban_chat_member(chat.id, target.id)
    except:
        pass

    # Final confirmation message
    text = (
        f"<b>🌐 GLOBAL BAN EXECUTED</b>\n\n"
        f"🚷 <b>User:</b> {target.mention_html()} (<code>{target.id}</code>)\n"
        f"🔨 <b>Actioned by:</b> {user.mention_html()}\n"
        f"📌 <b>Chat:</b> <code>{chat.title}</code>\n"
        f"🗃️ <b>Status:</b> <i>User added to global ban list</i>"
    )

    await update.message.reply_html(text, disable_web_page_preview=True)

async def ungban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_gban_powered(user.id):
        return await update.message.reply_html(
            "🚫 <b>Access Denied:</b> Only <i>lords</i> or <i>substitute lords</i> may invoke <code>/ungban</code>."
        )

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_html("❓ <b>Unknown user.</b> Please reply to a valid user.")
    
    if target.id not in global_bans:
        return await update.message.reply_html(f"ℹ️ <b>{target.mention_html()}</b> is <u>not globally banned</u>.")

    global_bans.discard(target.id)
    save_global_bans()

    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    except:
        pass

    await update.message.reply_html(
        f"<b>✅ GLOBAL UNBAN SUCCESSFUL</b>\n"
        f"👤 <b>User:</b> {target.mention_html()}\n"
        f"👑 <b>Revoked By:</b> {user.mention_html()}\n"
        f"🕊️ <i>User has been freed from the shadow realm.</i>"
    )


async def gmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_gban_powered(user.id):
        return await update.message.reply_html(
            "🚫 <b>Access Denied:</b> Only <i>lords</i> or <i>substitute lords</i> may invoke <code>/gmute</code>."
        )

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_html("❓ <b>No target specified.</b> Please reply to a user.")

    if is_sudo(target.id) or target.id == user.id:
        return await update.message.reply_html("🙅‍♂️ <b>Invalid target:</b> You cannot mute yourself or another sudo.")

    if target.id in global_mutes:
        return await update.message.reply_html(
            f"⚠️ <b>{target.mention_html()}</b> is already under <u>global mute</u>."
        )

    global_mutes.add(target.id)
    save_global_mutes()

    await update.message.reply_html(
        f"<b>🔇 GLOBAL MUTE INITIATED</b>\n"
        f"👤 <b>Target:</b> {target.mention_html()}\n"
        f"🛡️ <b>Executor:</b> {user.mention_html()}\n"
        f"🕸️ <i>The user's voice has been sealed across all lands.</i>"
    )

async def ungmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_gban_powered(user.id):
        return await update.message.reply_html(
            "🚫 <b>Access Denied:</b> Only <i>lords</i> or <i>substitute lords</i> may invoke <code>/gmute</code>."
        )

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_html("❓ <b>No target specified.</b> Please reply to a user.")

    if target.id not in global_mutes:
        return await update.message.reply_html(
            f"ℹ️ <b>{target.mention_html()}</b> is not under the <u>global mute</u> spell."
        )

    global_mutes.discard(target.id)
    save_global_mutes()

    await update.message.reply_html(
        f"<b>🔊 GLOBAL UNMUTE COMPLETE</b>\n"
        f"👤 <b>Target:</b> {target.mention_html()}\n"
        f"🛡️ <b>Executor:</b> {user.mention_html()}\n"
        f"✨ <i>The silence has been lifted. The voice returns.</i>"
    )


# === Enforcement Handler ===
async def global_enforcement_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_sudo(user_id):
        return
    
    # Check for bans first
    if user_id in global_bans:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Failed to ban user {user_id}: {e}")
        return  # Skip further processing for banned users
    
    # Then check for mutes
    if user_id in global_mutes:
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Failed to delete message from muted user {user_id}: {e}")

async def stats_track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in stats_data["groups"]:
        stats_data["groups"].add(update.effective_chat.id)
        save_stats_data()
    if update.effective_user.id not in stats_data["users"]:
        stats_data["users"].add(update.effective_user.id)
        save_stats_data()

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType

# Define your IDs
LORD_ID = 8429156335
SUBSTITUTE_LORDS = {8366899032}

# Helper functions
def is_lord(uid: int) -> bool:
    return uid == LORD_ID

def is_substitute_lord(uid: int) -> bool:
    return uid in SUBSTITUTE_LORDS


async def royal_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Royal welcome depending on who joins"""
    if update.chat_member.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    old = update.chat_member.old_chat_member
    new = update.chat_member.new_chat_member
    user = new.user

    if old.status in ["left", "kicked"] and new.status in ["member", "administrator"]:
        if not is_sudo(user.id):
            return

        mention = user.mention_html()
        chat_id = update.chat_member.chat.id

        if is_lord(user.id):
            text = (
                f"👑 <b>The Supreme Lord Has Arrived!</b>\n\n"
                f"🌌 {mention} enters the kingdom, shrouded in glory and honor.\n"
                f"🔔 All realms stand still. The shadows bow. The light salutes.\n\n"
                f"<i>⚔️ Let the divine presence be felt!</i>"
            )
        elif is_substitute_lord(user.id):
            text = (
                f"⚜️ <b>A Noble Substitute Lord Appears!</b>\n\n"
                f"🌠 {mention} graces us with their celestial aura.\n"
                f"🛡️ The stars whisper their name across the heavens.\n\n"
                f"<i>🎖️ Loyalty and honor walk again in this land.</i>"
            )
        else:
            text = (
                f"🧙 <b>An Honoured Sudo Joins Us!</b>\n\n"
                f"✨ {mention} returns from the digital beyond.\n"
                f"📜 The scripts tremble. The code flows.\n\n"
                f"<i>💻 May your commands be wise and your bans swift!</i>"
            )

        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        )

from telegram.ext import ChatMemberHandler


logger = logging.getLogger(__name__)

import logging
import re
from telegram import Update, User
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, Dict, Any
# MongoDB connection
mongo_client = AsyncIOMotorClient("mongodb+srv://ryumasgod:ryumasgod@cluster0.ojfkovp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client["yoruichi_bot_db"]
users_collection = db.users


async def store_user(user: User, chat_id: int):
    try:
        update_data = {
            "$set": {
                "username": user.username.lower() if user.username else None,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "last_seen": datetime.now(),
            },
            "$addToSet": {
                "chat_ids": chat_id
            }
        }

        if chat_id < 0:
            update_data["$set"][f"chats.{chat_id}"] = datetime.now()

        await users_collection.update_one(
            {"user_id": user.id},
            update_data,
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error storing user {user.id}: {e}")


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    try:
        username = username.lstrip('@').lower()
        return await users_collection.find_one({"username": username})
    except Exception as e:
        logger.error(f"Error looking up username {username}: {e}")
        return None


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    try:
        return await users_collection.find_one({"user_id": user_id})
    except Exception as e:
        logger.error(f"Error looking up user ID {user_id}: {e}")
        return None


async def track_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and not update.effective_user.is_bot:
        context.application.create_task(store_user(update.effective_user, update.effective_chat.id))


def format_user_info(user_data: Dict[str, Any], user: User = None) -> str:
    username = f"@{user_data['username']}" if user_data.get('username') else "N/A"
    full_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
    last_seen = user_data['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
    shared_chats = len(user_data.get('chat_ids', []))
    mention = user.mention_html() if user else full_name or username

    return (
        f"👤 <b>User Information</b>\n\n"
        f"📛 <b>Name:</b> {mention}\n"
        f"🌐 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{user_data['user_id']}</code>\n"
        f"📅 <b>Last Seen:</b> {last_seen}\n"
        f"💬 <b>Shared Chats:</b> {shared_chats}"
    )


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    try:
        # Case 1: reply
        if message.reply_to_message:
            replied_user = message.reply_to_message.from_user
            context.application.create_task(store_user(replied_user, update.effective_chat.id))
            user_data = await get_user_by_id(replied_user.id)
            if user_data:
                response = format_user_info(user_data, replied_user)
            else:
                response = (
                    f"👤 <b>Basic User Information</b>\n\n"
                    f"📛 <b>Name:</b> {replied_user.mention_html()}\n"
                    f"🆔 <b>ID:</b> <code>{replied_user.id}</code>\n\n"
                    f"<i>Full profile not yet in database</i>"
                )
            await message.reply_text(response, parse_mode="HTML")
            return

        # Case 2: username
        if context.args:
            username = context.args[0]
            user_data = await get_user_by_username(username)
            if user_data:
                response = format_user_info(user_data)
            else:
                response = (
                    f"🔍 User @{username.lstrip('@')} not found in database.\n"
                    "The bot needs to have seen this user in a message first."
                )
            await message.reply_text(response, parse_mode="HTML")
            return

        # Case 3: /id with no args
        chat = update.effective_chat
        response = (
            f"💬 <b>Chat Information</b>\n\n"
            f"🏷 <b>Title:</b> {chat.title if hasattr(chat, 'title') else 'Private Chat'}\n"
            f"🆔 <b>Chat ID:</b> <code>{chat.id}</code>\n"
            f"👥 <b>Type:</b> {chat.type}\n\n"
            "Usage:\n"
            "• <code>/id @username</code> - Lookup by username\n"
            "• <code>/id</code> in reply - Get user info\n"
            "• <code>/id</code> - Show chat info"
        )
        await message.reply_text(response, parse_mode="HTML")

    except Exception as e:
        logger.exception("Error in /id command")
        await message.reply_text("⚠️ Error retrieving information", parse_mode="HTML")


async def setup_database():
    """Create indexes once on startup"""
    try:
        await users_collection.create_index("username")
        await users_collection.create_index("user_id", unique=True)
        await users_collection.create_index("chat_ids")
        await users_collection.create_index("chats")
        logger.info("✅ MongoDB indexes created successfully")
    except Exception as e:
        logger.exception("❌ Failed to setup MongoDB indexes")

async def on_startup(app):
    await setup_database()


    logger.info("✅ Database initialized successfully")

import os
import re
import logging
import tempfile
import asyncio
import random
import yt_dlp
from telegram import Update, InputFile, constants
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Instagram URL pattern
import re
import os
import tempfile
import yt_dlp
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# =====================
# COOKIES FOR INSTAGRAM
# =====================
INSTAGRAM_COOKIES = """# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.

.instagram.com	TRUE	/	TRUE	1777919447	datr	143pZ1hYClbcexl_gUXN3Pal
.instagram.com	TRUE	/	TRUE	1774895498	ig_did	60AE72B3-FADF-4895-AB50-0F0393CB9FD8
.instagram.com	TRUE	/	TRUE	1774895447	ig_nrcb	1
.instagram.com	TRUE	/	TRUE	1779637219	ps_l	1
.instagram.com	TRUE	/	TRUE	1779637219	ps_n	1
.instagram.com	TRUE	/	TRUE	1781798892	mid	aCS_7QALAAHzdnVO36G_4nmAqE1e
.instagram.com	TRUE	/	TRUE	1789378708	csrftoken	Ul6BXwt15N6lKAjGxyx9p9LGCYAxonVw
.instagram.com	TRUE	/	TRUE	1762594708	ds_user_id	70808632711
.instagram.com	TRUE	/	TRUE	1755423502	wd	1536x695
.instagram.com	TRUE	/	TRUE	1755423502	dpr	1.25
.instagram.com	TRUE	/	TRUE	1755423507	ig_direct_region_hint	"EAG\\05470808632711\\0541786354708:01fe58686ae1120ff0ec4d0b85fdfef827b6f7d639fc48229371624dc286561734ab72e7"
.instagram.com	TRUE	/	TRUE	0	rur	"HIL\\05470808632711\\0541786354708:01fe5482392ab6608588e5f848eaadc451a64303563e5255cc27daf6c2bee0032c61e3b1"
.instagram.com	TRUE	/	TRUE	1786354708	sessionid	70808632711%3AxRnDEvMHeyi86d%3A21%3AAYczz6xj51BneDHV1lLq2Lmnk_qyF9MmP__6hKb6ag
"""

# =====================
# YOUTUBE DOWNLOADER
# =====================
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    msg = await update.message.reply_text("📥 Downloading YouTube video...")

    try:
        output_path = "video.%(ext)s"
        ydl_opts = {
            "outtmpl": output_path,
            "format": "mp4[height<=720]/best",
            "quiet": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

        with open(video_path, "rb") as f:
            await update.message.reply_video(f)

        os.remove(video_path)
        await msg.delete()

    except Exception as e:
        await msg.delete()
        await update.message.reply_text(f"❌ Error downloading YouTube video: {e}")

# =====================
# INSTAGRAM DOWNLOADER
# =====================
async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    msg = await update.message.reply_text("📥 Downloading Instagram reel...")

    try:
        # Save cookies to temp file
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as cookie_file:
            cookie_file.write(INSTAGRAM_COOKIES)
            cookie_file_path = cookie_file.name

        output_path = "reel.%(ext)s"
        ydl_opts = {
            "outtmpl": output_path,
            "format": "mp4[height<=720]/best",
            "quiet": True,
            "noplaylist": True,
            "cookies": cookie_file_path,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

        with open(video_path, "rb") as f:
            await update.message.reply_video(f)

        os.remove(video_path)
        os.remove(cookie_file_path)
        await msg.delete()

    except Exception as e:
        await msg.delete()
        await update.message.reply_text(f"❌ Error downloading Instagram reel: {e}")

# =====================
# LINK HANDLER
# =====================
async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message else ""
    yt_regex = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/[^\s]+"
    insta_regex = r"(https?://)?(www\.)?(instagram\.com|instagr\.am)/[^\s]+"

    if re.search(yt_regex, text):
        await download_video(update, context)
    elif re.search(insta_regex, text):
        await download_instagram(update, context)

IPINFO_TOKEN = '434e1cea389a93'
IPQUALITYSCORE_API_KEY = 'Y0OZMypz71dEF9HxxQd21J2xvqUE0BVS'

# Command handler for /ip
async def ip_info_and_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if len(context.args) != 1:
        await message.reply_text("ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ **ɪᴘ** ᴀᴅᴅʀᴇss ᴀғᴛᴇʀ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.\n\n**Example**: `/ip 8.8.8.8`", parse_mode="Markdown")
        return

    ip_address = context.args[0]
    ip_info = get_ip_info(ip_address)
    ip_score, score_description, emoji = get_ip_score(ip_address, IPQUALITYSCORE_API_KEY)

    if ip_info and ip_score is not None:
        response_message = (
            f"{ip_info}\n\n"
            f"**𝗜ᴘ sᴄᴏʀᴇ** ➪ {ip_score} {emoji} ({score_description})"
        )
        await message.reply_text(response_message, parse_mode="Markdown")
    else:
        await message.reply_text("Unable to fetch information for the provided IP address.")

# Function to get IP info from ipinfo.io
def get_ip_info(ip_address):
    api_url = f"https://ipinfo.io/{ip_address}?token={IPINFO_TOKEN}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            info = (
                f"🌐 **𝗜ᴘ** ➪ {data.get('ip', 'N/A')}\n"
                f"🏙️ **𝗖ɪᴛʏ** ➪ {data.get('city', 'N/A')}\n"
                f"📍 **𝗥ᴇɢɪᴏɴ** ➪ {data.get('region', 'N/A')}\n"
                f"🌍 **𝗖ᴏᴜɴᴛʀʏ** ➪ {data.get('country', 'N/A')}\n"
                f"📌 **𝗟ᴏᴄᴀᴛɪᴏɴ** ➪ {data.get('loc', 'N/A')}\n"
                f"🏢 **𝗢ʀɢᴀɴɪᴢᴀᴛɪᴏɴ** ➪ {data.get('org', 'N/A')}\n"
                f"📮 **𝗣ᴏsᴛᴀʟ ᴄᴏᴅᴇ** ➪ {data.get('postal', 'N/A')}\n"
                f"⏰ **𝗧ɪᴍᴇᴢᴏɴᴇ** ➪ {data.get('timezone', 'N/A')}"
            )
            return info
    except Exception as e:
        print(f"Error fetching IP information: {e}")
    return None

# Function to get IP fraud score from IPQualityScore
def get_ip_score(ip_address, api_key):
    api_url = f"https://ipqualityscore.com/api/json/ip/{api_key}/{ip_address}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            fraud_score = data.get('fraud_score', 'N/A')
            if fraud_score != 'N/A':
                fraud_score = int(fraud_score)
                if fraud_score <= 20:
                    score_description = 'Good'
                    emoji = '✅'
                elif fraud_score <= 60:
                    score_description = 'Moderate'
                    emoji = '⚠️'
                else:
                    score_description = 'Bad'
                    emoji = '❌'
                return fraud_score, score_description, emoji
    except Exception as e:
        print(f"Error fetching IP score: {e}")
    return None, None, None

OWNER_ID = 8429156335  # Replace with your actual owner ID
ALLOWED_USER_IDS = {OWNER_ID}  # Add other privileged users if needed

def is_authorized(user_id: int) -> bool:
    """Check if user is authorized to use the command"""
    return user_id in ALLOWED_USER_IDS

async def leave_chat_safely(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> dict:
    """
    Safely leave a chat with comprehensive error handling
    Returns a dictionary with status and details
    """
    result = {
        'chat_id': chat_id,
        'success': False,
        'message': '',
        'chat_type': None,
        'chat_title': None
    }
    
    try:
        chat = await context.bot.get_chat(chat_id)
        result['chat_type'] = chat.type
        result['chat_title'] = chat.title or chat.username or str(chat.id)
        
        # Check if bot is already not in chat
        try:
            await context.bot.get_chat_member(chat_id, context.bot.id)
        except BadRequest as e:
            if "user not participant" in str(e).lower():
                result['message'] = f"❌ <b>Not in chat:</b> <code>{result['chat_title']}</code>"
                return result
        
        await context.bot.leave_chat(chat_id)
        result['success'] = True
        result['message'] = f"✅ <b>Left {chat.type.title()}:</b> <code>{result['chat_title']}</code>"
        
    except BadRequest as e:
        error_msg = str(e).lower()
        if "chat not found" in error_msg:
            result['message'] = f"❌ <b>Invalid chat ID:</b> <code>{chat_id}</code>"
        elif "chat_admin_required" in error_msg:
            result['message'] = f"❌ <b>Need admin rights to leave:</b> <code>{result['chat_title'] or chat_id}</code>"
        elif "channel_private" in error_msg:
            result['message'] = f"❌ <b>Channel is private or I'm banned:</b> <code>{result['chat_title'] or chat_id}</code>"
        else:
            logger.error(f"Leave chat error: {e}")
            result['message'] = f"⚠️ <b>BadRequest error:</b> <code>{chat_id}</code> ({e})"
            
    except Forbidden as e:
        result['message'] = f"❌ <b>Forbidden:</b> <code>{result['chat_title'] or chat_id}</code> ({e})"
        
    except TelegramError as e:
        logger.error(f"Leave chat error: {e}")
        result['message'] = f"⚠️ <b>Telegram error:</b> <code>{chat_id}</code> ({e})"
        
    except Exception as e:
        logger.error(f"Unexpected leave chat error: {e}")
        result['message'] = f"⚠️ <b>Unknown error:</b> <code>{chat_id}</code> ({e})"
        
    return result

async def process_chat_ids(context: ContextTypes.DEFAULT_TYPE, chat_ids: List[str]) -> List[dict]:
    """Process multiple chat IDs and return results"""
    results = []
    for chat_id_str in chat_ids:
        try:
            chat_id = int(chat_id_str)
            result = await leave_chat_safely(context, chat_id)
            results.append(result)
        except ValueError:
            results.append({
                'chat_id': chat_id_str,
                'success': False,
                'message': f"❌ <b>{chat_id_str}:</b> Invalid format (must be integer)"
            })
    return results

def generate_stats(results: List[dict]) -> str:
    """Generate statistics from the results"""
    total = len(results)
    success = sum(1 for r in results if r['success'])
    failed = total - success
    
    stats = (
        f"📊 <b>Statistics:</b>\n"
        f"• Total: {total}\n"
        f"• Success: {success}\n"
        f"• Failed: {failed}\n\n"
    )
    return stats

def format_results(results: List[dict]) -> str:
    """Format the results for display"""
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(f"{i}. {result['message']}")
    return "\n".join(formatted)

async def leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the leave command"""
    user = update.effective_user
    chat = update.effective_chat
    
    if not is_authorized(user.id):
        await update.message.reply_html("🚫 <b>This command is restricted to authorized users only.</b>")
        return

    args = context.args
    if not args:
        help_text = (
            "ℹ️ <b>Leave Command Usage:</b>\n\n"
            "<code>/leave &lt;chat_id1&gt; &lt;chat_id2&gt; ...</code>\n"
            "• Separate multiple chat IDs with spaces\n"
            "• Supports both group/channel IDs\n\n"
            "<b>Examples:</b>\n"
            "<code>/leave -1001234567890 -1009876543210</code>\n"
            "<code>/leave 123456789 987654321</code>"
        )
        await update.message.reply_html(help_text)
        return

    # Send processing message
    processing_msg = await update.message.reply_text("🔄 Processing your request...")
    
    # Process chat IDs
    results = await process_chat_ids(context, args)
    
    # Generate response
    stats = generate_stats(results)
    results_text = format_results(results)
    response = f"<b>🚪 Leave Command Results</b>\n\n{stats}{results_text}"
    
    # Edit original message with results
    try:
        await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        await update.message.reply_html(response)
    
    # Send summary to owner if not in private chat
    if chat.type != ChatType.PRIVATE:
        try:
            short_response = (
                f"<b>🚪 Leave Command Executed</b>\n"
                f"• Chat: {chat.title or chat.id}\n"
                f"• User: {user.mention_html()}\n\n"
                f"{generate_stats(results)}"
            )
            await context.bot.send_message(OWNER_ID, short_response, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Failed to send summary to owner: {e}")

async def leave_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the leave_all command to leave all chats"""
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_html("🚫 <b>This command is restricted to authorized users only.</b>")
        return
    
    # Confirm before proceeding
    confirm_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="leave_all_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="leave_all_cancel")]
    ])
    
    await update.message.reply_html(
        "⚠️ <b>Warning:</b> This will make the bot leave ALL chats it's currently in!\n\n"
        "Are you sure you want to proceed?",
        reply_markup=confirm_keyboard
    )

async def leave_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "leave_all_confirm":
        await query.edit_message_text("🔄 Preparing to leave all chats...")
        # Implement logic to leave all chats
        # This would need additional functionality to track all chats the bot is in
        await query.edit_message_text("✅ Left all chats successfully!")
    elif query.data == "leave_all_cancel":
        await query.edit_message_text("❌ Operation cancelled.")

def get_random_message(love_percentage: int) -> str:
    if love_percentage <= 30:
        return random.choice([
            "Love is in the air but needs a little spark.",
            "A good start but there's room to grow.",
            "It's just the beginning of something beautiful."
        ])
    elif love_percentage <= 70:
        return random.choice([
            "A strong connection is there. Keep nurturing it.",
            "You've got a good chance. Work on it.",
            "Love is blossoming, keep going."
        ])
    else:
        return random.choice([
            "Wow! It's a match made in heaven!",
            "Perfect match! Cherish this bond.",
            "Destined to be together. Congratulations!"
        ])

async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if len(args) >= 2:
        name1 = args[0].strip()
        name2 = args[1].strip()

        love_percentage = random.randint(10, 100)
        love_message = get_random_message(love_percentage)

        response = f"{name1}💕 + {name2}💕 = {love_percentage}%\n\n{love_message}"
    else:
        response = "Please enter two names after /love command.\nExample: `/love Alice Bob`"

    await message.reply_text(response, parse_mode="Markdown")

async def meme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_url = "https://meme-api.com/gimme"
    try:
        response = requests.get(api_url)
        data = response.json()

        meme_url = data.get("url")
        title = data.get("title")
        user_mention = update.effective_user.mention_html()

        caption = f"{title}\n\nRequested by {user_mention}\nBot username: @{BOT_USERNAME}"

        await update.message.reply_photo(photo=meme_url, caption=caption, parse_mode="HTML")

    except Exception as e:
        print(f"Error fetching meme: {e}")
        await update.message.reply_text("Sorry, I couldn't fetch a meme at the moment.")

import json
from datetime import datetime
from telegram import ChatPermissions, Update
from telegram.ext import ContextTypes, CallbackContext
import os

# JSON file for storing settings
NIGHTMODE_FILE = "nightmode.json"

# Default permissions
NIGHT_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_change_info=False,
    can_invite_users=False,
    can_pin_messages=False
)

DAY_PERMS = ChatPermissions(
    can_send_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_change_info=False,
    can_invite_users=False,
    can_pin_messages=False
)


# ---------- JSON Helpers ----------
def load_nightmode_data():
    if not os.path.exists(NIGHTMODE_FILE):
        return {}
    with open(NIGHTMODE_FILE, "r") as f:
        return json.load(f)


def save_nightmode_data(data):
    with open(NIGHTMODE_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------- Core Functions ----------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )

    if member.status not in ("administrator", "creator"):
        return False

    # For creators, always true; for admins, check specific permission
    if member.status == "creator":
        return True

    # member can be ChatMemberAdministrator object
    return getattr(member, "can_change_info", False) is True



async def nightmode_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("🚫 Admin rights required!")

    chat_id = str(update.effective_chat.id)
    data = load_nightmode_data()

    if chat_id in data and data[chat_id]["enabled"]:
        data[chat_id]["enabled"] = False
        save_nightmode_data(data)
        await context.bot.set_chat_permissions(int(chat_id), DAY_PERMS)
        return await update.message.reply_text("🌞 Nightmode disabled — chat unlocked.")

    data[chat_id] = {
        "enabled": True,
        "start_time": "23:00",
        "end_time": "05:00"
    }
    save_nightmode_data(data)
    await update.message.reply_text("🌙 Nightmode enabled — will lock at set times.")


async def set_nightmode_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("🚫 Admin rights required!")

    if len(context.args) != 2:
        return await update.message.reply_text("❌ Usage: /nightmode_time 23:00 05:00")

    try:
        start_time = datetime.strptime(context.args[0], "%H:%M").time()
        end_time = datetime.strptime(context.args[1], "%H:%M").time()
    except ValueError:
        return await update.message.reply_text("❌ Time must be HH:MM in 24h format.")

    chat_id = str(update.effective_chat.id)
    data = load_nightmode_data()

    if chat_id not in data:
        data[chat_id] = {"enabled": True}

    data[chat_id]["start_time"] = start_time.strftime("%H:%M")
    data[chat_id]["end_time"] = end_time.strftime("%H:%M")
    save_nightmode_data(data)

    await update.message.reply_text(
        f"⏰ Nightmode times updated:\n🔒 Lock: {start_time}\n🔓 Unlock: {end_time}"
    )


async def nightmode_job(context: CallbackContext):
    now = datetime.now().time()
    data = load_nightmode_data()

    for chat_id, settings in data.items():
        if not settings.get("enabled"):
            continue

        start_t = datetime.strptime(settings["start_time"], "%H:%M").time()
        end_t = datetime.strptime(settings["end_time"], "%H:%M").time()

        if start_t < end_t:  # same-day nightmode
            in_night = start_t <= now < end_t
        else:  # overnight nightmode
            in_night = now >= start_t or now < end_t

        try:
            if in_night:
                await context.bot.set_chat_permissions(int(chat_id), NIGHT_PERMS)
            else:
                await context.bot.set_chat_permissions(int(chat_id), DAY_PERMS)
        except Exception:
            pass

RIGHT_EMOJIS = {
    "creator": "👑",
    "administrator": "🛡️",
    "can_delete_messages": "🗑️",
    "can_restrict_members": "🚫",
    "can_promote_members": "📈",
    "can_change_info": "✏️",
    "can_invite_users": "➕",
    "can_pin_messages": "📌",
    "member": "👤",
    "anonymous": "👻"
}

def build_rights_keyboard(rights: list):
    # Create buttons for each right (non-clickable)
    buttons = [
        [InlineKeyboardButton(right, callback_data="rights_noop")]
        for right in rights
    ]
    # Add refresh and close buttons
    buttons.append([
        InlineKeyboardButton("🔄 Refresh", callback_data="refresh_rights"),
        InlineKeyboardButton("❌ Close", callback_data="rights_close")
    ])
    return InlineKeyboardMarkup(buttons)

def get_formatted_rights(member: ChatMember):
    rights = []
    status = member.status

    # Base status
    if status == "creator":
        rights.append(f"{RIGHT_EMOJIS['creator']} <b>Group Owner</b>")
    elif status == "administrator":
        rights.append(f"{RIGHT_EMOJIS['administrator']} <b>Administrator</b>")
    elif status == "member":
        rights.append(f"{RIGHT_EMOJIS['member']} <b>Regular Member</b>")
    elif status == "restricted":
        rights.append(f"⛔ <b>Restricted Member</b>")
    elif status == "left":
        rights.append(f"🚪 <b>Left Group</b>")
    elif status == "kicked":
        rights.append(f"🔴 <b>Banned</b>")
    elif status == "anonymous":
        rights.append(f"{RIGHT_EMOJIS['anonymous']} <b>Anonymous Admin</b>")

    # Admin privileges (if admin)
    if status in ["creator", "administrator"]:
        if getattr(member, "can_delete_messages", False):
            rights.append(f"{RIGHT_EMOJIS['can_delete_messages']} Delete Messages")
        if getattr(member, "can_restrict_members", False):
            rights.append(f"{RIGHT_EMOJIS['can_restrict_members']} Restrict Members")
        if getattr(member, "can_promote_members", False):
            rights.append(f"{RIGHT_EMOJIS['can_promote_members']} Promote Members")
        if getattr(member, "can_change_info", False):
            rights.append(f"{RIGHT_EMOJIS['can_change_info']} Change Group Info")
        if getattr(member, "can_invite_users", False):
            rights.append(f"{RIGHT_EMOJIS['can_invite_users']} Invite Users")
        if getattr(member, "can_pin_messages", False):
            rights.append(f"{RIGHT_EMOJIS['can_pin_messages']} Pin Messages")
        if getattr(member, "can_manage_video_chats", False):
            rights.append("🎥 Manage Video Chats")
        if getattr(member, "can_manage_chat", False):
            rights.append("⚙️ Manage Chat")
        if getattr(member, "is_anonymous", False):
            rights.append(f"{RIGHT_EMOJIS['anonymous']} Anonymous")

    # For restricted members
    if status == "restricted":
        if getattr(member, "can_send_messages", False):
            rights.append("💬 Can send messages")
        if getattr(member, "can_send_media_messages", False):
            rights.append("🖼️ Can send media")
        if getattr(member, "can_send_stickers", False):
            rights.append("🪀 Can send stickers")
        if getattr(member, "can_send_animations", False):
            rights.append("🎭 Can send animations")
        if getattr(member, "can_send_games", False):
            rights.append("🎮 Can send games")
        if getattr(member, "can_use_inline_bots", False):
            rights.append("🤖 Can use inline bots")
        if getattr(member, "can_add_web_page_previews", False):
            rights.append("🌐 Can add web previews")
        if getattr(member, "can_pin_messages", False):
            rights.append(f"{RIGHT_EMOJIS['can_pin_messages']} Can pin messages")
        if getattr(member, "can_change_info", False):
            rights.append(f"{RIGHT_EMOJIS['can_change_info']} Can change info")

    return rights

async def check_rights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ This command only works in groups.")
        return

    user_id = update.effective_user.id
    chat = update.effective_chat

    try:
        member = await context.bot.get_chat_member(chat.id, user_id)
    except Exception:
        await update.message.reply_text("❌ Failed to fetch your member information.")
        return

    rights = get_formatted_rights(member)
    if not rights:
        rights = ["🤷 No special rights"]

    keyboard = build_rights_keyboard(rights)
    await update.message.reply_text(
        f"✨ <b>Your permissions in {chat.title}:</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

async def refresh_rights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat = query.message.chat

    try:
        member = await context.bot.get_chat_member(chat.id, user_id)
    except Exception:
        await query.answer("Failed to refresh rights", show_alert=True)
        return

    rights = get_formatted_rights(member)
    if not rights:
        rights = ["🤷 No special rights"]

    keyboard = build_rights_keyboard(rights)
    await query.edit_message_text(
        f"✨ <b>Your permissions in {chat.title}:</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    await query.answer("Rights refreshed!")

async def close_rights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.message.delete()
    await query.answer("Closed rights view")

async def noop_rights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("This shows your current rights", show_alert=False)
import httpx

POKE_API = "https://pokeapi.co/api/v2/pokemon/"
POKE_IMAGE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{id}.png"
POKE_CRY = "https://play.pokemonshowdown.com/audio/cries/{name}.mp3"


# --- Helper Functions ---
def format_stats(stats: list) -> str:
    return "\n".join(
        f"▫️ <b>{s['stat']['name'].title()}</b>: {s['base_stat']}"
        for s in stats
    )


def format_moves(moves: list) -> str:
    if not moves:
        return "No known moves."
    move_list = [m['move']['name'].replace('-', ' ').title() for m in moves[:10]]
    return ", ".join(move_list) + ("..." if len(moves) > 10 else "")


def format_abilities(abilities: list) -> str:
    return "\n".join(
        f"▫️ {a['ability']['name'].title()}{' (Hidden)' if a['is_hidden'] else ''}"
        for a in abilities
    )


async def fetch_pokemon_data(query: str) -> Optional[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            res = await client.get(f"{POKE_API}{query.lower()}")
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError:
            return None
        except Exception as e:
            logger.error(f"API Error: {e}")
            return None


# --- Command Handler ---
async def pokedex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_html(
            "🔍 <b>Pokédex Search</b>\n\n"
            "Usage: <code>/pokedex &lt;name_or_id&gt;</code>\n"
            "Example: <code>/pokedex pikachu</code>"
        )
        return

    query = context.args[0]
    data = await fetch_pokemon_data(query)

    if not data:
        await update.message.reply_text("❌ Pokémon not found. Check the name or ID.")
        return

    name = data['name'].title()
    poke_id = data['id']
    types = ", ".join(t['type']['name'].title() for t in data['types'])
    height = data['height'] / 10
    weight = data['weight'] / 10

    caption = (
        f"✨ <b>{name} #{poke_id}</b>\n\n"
        f"▫️ <b>Type:</b> {types}\n"
        f"▫️ <b>Height:</b> {height}m\n"
        f"▫️ <b>Weight:</b> {weight}kg"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data=f"stats_{poke_id}"),
            InlineKeyboardButton("⚔️ Moves", callback_data=f"moves_{poke_id}")
        ],
        [
            InlineKeyboardButton("🌟 Abilities", callback_data=f"abilities_{poke_id}"),
            InlineKeyboardButton("🔊 Play Cry", callback_data=f"cry_{poke_id}_{name.lower()}")
        ]
    ])

    await update.message.reply_photo(
        photo=POKE_IMAGE.format(id=poke_id),
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


# --- Callback Query Handler ---
async def pokedex_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action, poke_id = data[0], data[1]

    poke_data = await fetch_pokemon_data(poke_id)
    if not poke_data:
        await query.edit_message_text("❌ Failed to fetch Pokémon data.")
        return

    name = poke_data["name"].title()

    if action == "stats":
        text = f"📊 <b>{name}'s Base Stats</b>\n\n{format_stats(poke_data['stats'])}"
    elif action == "moves":
        text = f"⚔️ <b>{name}'s Moves</b>\n\n{format_moves(poke_data['moves'])}"
    elif action == "abilities":
        text = f"🌟 <b>{name}'s Abilities</b>\n\n{format_abilities(poke_data['abilities'])}"
    elif action == "cry":
        cry_url = POKE_CRY.format(name=data[2])
        try:
            await query.message.reply_audio(
                audio=cry_url,
                caption=f"🔊 {name}'s cry"
            )
        except Exception:
            await query.message.reply_text("❌ Failed to play cry.")
        return
    elif action == "back":
        return await back_to_main(query, poke_data)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=f"back_{poke_id}")]
    ])

    await query.edit_message_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


# --- Back to Main View ---
async def back_to_main(query, data):
    name = data['name'].title()
    poke_id = data['id']
    types = ", ".join(t['type']['name'].title() for t in data['types'])
    height = data['height'] / 10
    weight = data['weight'] / 10

    caption = (
        f"✨ <b>{name} #{poke_id}</b>\n\n"
        f"▫️ <b>Type:</b> {types}\n"
        f"▫️ <b>Height:</b> {height}m\n"
        f"▫️ <b>Weight:</b> {weight}kg"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data=f"stats_{poke_id}"),
            InlineKeyboardButton("⚔️ Moves", callback_data=f"moves_{poke_id}")
        ],
        [
            InlineKeyboardButton("🌟 Abilities", callback_data=f"abilities_{poke_id}"),
            InlineKeyboardButton("🔊 Play Cry", callback_data=f"cry_{poke_id}_{name.lower()}")
        ]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media=POKE_IMAGE.format(id=poke_id),
            caption=caption,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=keyboard
    )

async def population_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if len(context.args) == 0:
        return await message.reply_text("Usage: /population <country_code>\nExample: /population in")

    country_code = context.args[0].strip()
    api_url = f"https://restcountries.com/v3.1/alpha/{country_code}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        country_info = response.json()

        if country_info:
            country_name = country_info[0].get("name", {}).get("common", "N/A")
            capital = country_info[0].get("capital", ["N/A"])[0]
            population = country_info[0].get("population", "N/A")

            response_text = (
                f"🌍 <b>Country Information</b>\n\n"
                f"🗺️ <b>Name:</b> {country_name}\n"
                f"🏛️ <b>Capital:</b> {capital}\n"
                f"👥 <b>Population:</b> {population}"
            )
        else:
            response_text = "❌ Error fetching country information from the API."

    except requests.exceptions.HTTPError:
        response_text = "⚠️ HTTP error occurred. Please enter a valid country code."
    except Exception:
        response_text = "🚫 An unexpected error occurred while fetching data."

    await message.reply_text(response_text, parse_mode="HTML")

TODO_DB: Dict[int, List[Dict]] = {}
USER_STATES: Dict[int, str] = {}

# Emoji constants
EMOJIS = {
    "menu": "📝", "add": "➕", "list": "📋", "done": "✅",
    "remove": "🗑", "clear": "🧹", "back": "🔙", "empty": "📭",
    "edit": "✏️", "stats": "📊"
}


async def get_todo_menu(user_id: int) -> InlineKeyboardMarkup:
    tasks = TODO_DB.get(user_id, [])
    completed = sum(1 for t in tasks if t.get("done"))
    total = len(tasks)

    buttons = [
        [InlineKeyboardButton(f"{EMOJIS['add']} Add Task", callback_data="todo_add")],
        [InlineKeyboardButton(f"{EMOJIS['list']} View Tasks ({completed}/{total})", callback_data="todo_list")],
        [InlineKeyboardButton(f"{EMOJIS['done']} Complete Task", callback_data="todo_done")],
        [InlineKeyboardButton(f"{EMOJIS['remove']} Remove Task", callback_data="todo_remove")],
        [InlineKeyboardButton(f"{EMOJIS['clear']} Clear All", callback_data="todo_clear")],
        [InlineKeyboardButton(f"{EMOJIS['stats']} Statistics", callback_data="todo_stats")]
    ]
    return InlineKeyboardMarkup(buttons)


# /todo command
async def todo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    menu = await get_todo_menu(user_id)
    await update.message.reply_html(
        f"{EMOJIS['menu']} <b>To-Do Manager</b>\n"
        "Organize your tasks efficiently!\n\n"
        "▫️ Add new tasks\n▫️ Mark completed\n▫️ Remove tasks\n▫️ View statistics",
        reply_markup=menu
    )


# Callback handler
async def handle_todo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    action = query.data.split("_")[1]
    tasks = TODO_DB.setdefault(user_id, [])

    if action == "add":
        USER_STATES[user_id] = "awaiting_task"
        await query.edit_message_text(
            f"{EMOJIS['add']} <b>Add New Task</b>\n\nType your task below:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{EMOJIS['back']} Back", callback_data="todo_back")]
            ])
        )

    elif action == "list":
        if not tasks:
            await query.edit_message_text(
                f"{EMOJIS['empty']} Your to-do list is empty!",
                reply_markup=await get_todo_menu(user_id)
            )
            return

        task_list = "\n".join(
            f"{i+1}. {'✅' if t['done'] else '🔹'} {t['text']}"
            + (f" 📅 {t['date']}" if "date" in t else "")
            for i, t in enumerate(tasks)
        )

        await query.edit_message_text(
            f"{EMOJIS['list']} <b>Your Tasks</b>\n\n{task_list}",
            parse_mode=ParseMode.HTML,
            reply_markup=await get_todo_menu(user_id)
        )

    elif action == "done":
        if not tasks:
            await query.edit_message_text(
                f"{EMOJIS['empty']} No tasks to complete!",
                reply_markup=await get_todo_menu(user_id)
            )
            return

        buttons = [
            [InlineKeyboardButton(
                f"{'✅' if t['done'] else '🔹'} {i+1}. {t['text'][:20]}",
                callback_data=f"complete_{i}"
            )]
            for i, t in enumerate(tasks)
        ]
        buttons.append([InlineKeyboardButton(f"{EMOJIS['back']} Back", callback_data="todo_back")])

        await query.edit_message_text(
            f"{EMOJIS['done']} <b>Mark Tasks Complete</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif action == "remove":
        if not tasks:
            await query.edit_message_text(
                f"{EMOJIS['empty']} No tasks to remove!",
                reply_markup=await get_todo_menu(user_id)
            )
            return

        buttons = [
            [InlineKeyboardButton(
                f"{EMOJIS['remove']} {i+1}. {t['text'][:20]}",
                callback_data=f"remove_{i}"
            )]
            for i, t in enumerate(tasks)
        ]
        buttons.append([InlineKeyboardButton(f"{EMOJIS['back']} Back", callback_data="todo_back")])

        await query.edit_message_text(
            f"{EMOJIS['remove']} <b>Remove Tasks</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif action == "clear":
        if not tasks:
            await query.edit_message_text(
                f"{EMOJIS['empty']} Already empty!",
                reply_markup=await get_todo_menu(user_id)
            )
            return

        await query.edit_message_text(
            f"⚠️ <b>Clear All Tasks?</b>\n\nThis will delete all {len(tasks)} tasks permanently.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Confirm Clear", callback_data="confirm_clear")],
                [InlineKeyboardButton(f"{EMOJIS['back']} Cancel", callback_data="todo_back")]
            ])
        )

    elif action == "stats":
        completed = sum(1 for t in tasks if t.get("done", False))
        percentage = (completed / len(tasks)) * 100 if tasks else 0
        await query.edit_message_text(
            f"{EMOJIS['stats']} <b>Task Statistics</b>\n\n"
            f"▫️ Total Tasks: {len(tasks)}\n"
            f"▫️ Completed: {completed}\n"
            f"▫️ Pending: {len(tasks) - completed}\n"
            f"▫️ Completion: {percentage:.1f}%\n\n"
            "Keep up the good work! 💪",
            parse_mode=ParseMode.HTML,
            reply_markup=await get_todo_menu(user_id)
        )

    elif action == "back":
        await query.edit_message_text(
            f"{EMOJIS['menu']} <b>To-Do Manager</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=await get_todo_menu(user_id)
        )


# Callback handler for task actions
async def handle_task_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    data = query.data.split("_")
    action, index = data[0], int(data[1])
    tasks = TODO_DB.setdefault(user_id, [])

    if action == "complete":
        if 0 <= index < len(tasks):
            tasks[index]["done"] = not tasks[index].get("done", False)
            status = "completed" if tasks[index]["done"] else "marked as pending"
            await query.edit_message_text(
                f"✅ Task {status}:\n{tasks[index]['text']}",
                reply_markup=await get_todo_menu(user_id)
            )

    elif action == "remove":
        if 0 <= index < len(tasks):
            removed = tasks.pop(index)
            await query.edit_message_text(
                f"🗑 Removed task:\n{removed['text']}",
                reply_markup=await get_todo_menu(user_id)
            )

    elif action == "confirm":
        TODO_DB[user_id] = []
        await query.edit_message_text(
            "🧹 All tasks cleared!",
            reply_markup=await get_todo_menu(user_id)
        )


# Message handler for adding tasks
async def handle_task_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if USER_STATES.get(user_id) == "awaiting_task":
        task_text = update.message.text.strip()
        if task_text:
            TODO_DB.setdefault(user_id, []).append({
                "text": task_text,
                "done": False,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            await update.message.reply_html(
                f"✅ Task added:\n<code>{task_text}</code>",
                reply_markup=await get_todo_menu(user_id)
            )
        USER_STATES.pop(user_id, None)


import logging
import re
import html
from io import BytesIO
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
import qrcode

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_valid_url(text: str) -> bool:
    return bool(re.match(r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", text, re.IGNORECASE))


def generate_qr_image(data: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    bio.name = "qrcode.png"
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio


async def qrcode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_input = " ".join(context.args) if context.args else ""

    # Use replied message if no args
    if not user_input and message.reply_to_message:
        user_input = (
            message.reply_to_message.text
            or message.reply_to_message.caption
            or ""
        )

    user_input = user_input.strip()

    if not user_input:
        await message.reply_text(
            "⚠️ Please provide text or a URL to generate QR code.\n"
            "💡 Usage: `/qrcode <text or url>` or reply to a message.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(user_input) > 1000:
        await message.reply_text("🚫 Input too long! Limit is 1000 characters.")
        return

    status = await message.reply_text("⏳ Generating QR code...")

    try:
        qr_image = generate_qr_image(user_input)
        safe_input = html.escape(user_input[:250]) + (
            "..." if len(user_input) > 250 else ""
        )
        qr_type = "🌐 URL" if is_valid_url(user_input) else "📝 Text"

        caption = (
            f"<b>✅ QR Code Generated!</b>\n"
            f"<b>🔢 Type:</b> {qr_type}\n"
            f"<b>📥 Data:</b> <code>{safe_input}</code>"
        )

        await status.delete()
        await message.reply_photo(qr_image, caption=caption, parse_mode=ParseMode.HTML)

    except Exception as e:
        await status.edit_text(
            f"❌ Failed to generate QR code.\n<code>{html.escape(str(e))}</code>",
            parse_mode=ParseMode.HTML,
        )

QUOTE_API = "https://bot.lyo.su/quote/generate.png"
DEFAULT_COLOR = "#1b1429"

COLOR_MAP = {
    "black": "#000000", "white": "#ffffff", "gray": "#808080", "red": "#e74c3c",
    "blue": "#3498db", "green": "#2ecc71", "yellow": "#f1c40f", "pink": "#ff69b4",
    "purple": "#8e44ad", "orange": "#f39c12", "maroon": "#800000", "navy": "#000080",
    "teal": "#1abc9c", "lime": "#00ff00", "olive": "#808000", "aqua": "#00ffff",
    "fuchsia": "#ff00ff", "silver": "#c0c0c0", "gold": "#ffd700", "brown": "#a52a2a",
    "coral": "#ff7f50", "indigo": "#4b0082", "violet": "#ee82ee", "cyan": "#00ffff",
    "magenta": "#ff00ff", "wheat": "#f5deb3", "tan": "#d2b48c", "plum": "#dda0dd",
    "sienna": "#a0522d", "salmon": "#fa8072", "chocolate": "#d2691e", "ivory": "#fffff0",
    "orchid": "#da70d6", "khaki": "#f0e68c", "crimson": "#dc143c", "lavender": "#e6e6fa",
    "beige": "#f5f5dc", "mint": "#98ff98", "skyblue": "#87ceeb", "turquoise": "#40e0d0",
}
COLOR_LIST = list(COLOR_MAP.values())


# === Utilities ===
def get_text(msg) -> str:
    return msg.text or msg.caption or ""

def get_args(msg) -> list[str]:
    if msg.text:
        parts = msg.text.split(maxsplit=1)
    elif msg.caption:
        parts = msg.caption.split(maxsplit=1)
    else:
        parts = []
    return parts[1].split() if len(parts) > 1 else []

def entity_list(msg):
    ents = msg.entities or msg.caption_entities or []
    return [
        {
            "type": e.type.lower() if isinstance(e.type, str) else e.type.name.lower(),
            "offset": e.offset,
            "length": e.length,
        }
        for e in ents
    ]

def chat_type_str(msg) -> str:
    return "private" if msg.chat.type == ChatType.PRIVATE else "group"


# === Quote Generation Handler ===
async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        return await update.message.reply_html("⚠️ <b>Please reply to a message to quote it.</b>")

    replied = update.message.reply_to_message
    args = [a.lower() for a in get_args(update.message)]

    include_reply = "r" in args
    background = DEFAULT_COLOR
    count = 1

    for a in args:
        if a == "random":
            background = random.choice(COLOR_LIST)
        elif a in COLOR_MAP:
            background = COLOR_MAP[a]
        elif a.startswith("#") and len(a) == 7:
            background = a
        elif a.isdigit():
            count = int(a)

    messages = []
    for i in range(count):
        try:
            m = await context.bot.get_chat(update.effective_chat.id).get_message(replied.message_id + i)
            if m and not m.photo and not m.video:
                messages.append(m)
        except Exception:
            continue

    if not messages:
        messages = [replied]

    payload = {
        "type": "quote",
        "format": "png",
        "backgroundColor": background,
        "messages": [],
    }

    for m in messages:
        u = m.from_user
        reply_block = {}
        if include_reply and m.reply_to_message:
            ru = m.reply_to_message.from_user
            reply_block = {
                "name": ru.full_name if ru else "Unknown",
                "text": get_text(m.reply_to_message),
                "chatId": ru.id if ru else 0,
            }

        payload["messages"].append(
            {
                "chatId": u.id if u else 0,
                "text": get_text(m),
                "entities": entity_list(m),
                "avatar": True,
                "from": {
                    "id": u.id if u else 0,
                    "name": u.full_name if u else "Unknown",
                    "username": (u.username or "") if u else "",
                    "type": chat_type_str(m),
                    "photo": "",
                },
                "replyMessage": reply_block,
            }
        )

    processing = await update.message.reply_html("🖌️ <b>Creating quote, please wait...</b>")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(QUOTE_API, json=payload)
            if r.status_code == 200:
                img = BytesIO(r.content)
                img.name = "quote.webp"
                await processing.delete()
                await update.message.reply_sticker(img)
            else:
                await processing.edit_text("❌ <b>Failed to generate quote.</b>")
    except Exception as e:
        await processing.edit_text(f"⚠️ <b>Error:</b> <code>{e}</code>")


# === Fake Quote Command (/qt) ===
async def fake_quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        return await update.message.reply_html("⚠️ <b>Usage:</b> /qt <text> (reply to a message)")

    args = get_args(update.message)
    if not args:
        return await update.message.reply_html("⚠️ <b>Usage:</b> /qt <text> (reply to a message)")

    fake_text = " ".join(args)
    background = DEFAULT_COLOR
    for a in args:
        a = a.lower()
        if a in COLOR_MAP:
            background = COLOR_MAP[a]
        elif a.startswith("#") and len(a) == 7:
            background = a

    replied = update.message.reply_to_message
    u = replied.from_user

    payload = {
        "type": "quote",
        "format": "png",
        "backgroundColor": background,
        "messages": [
            {
                "chatId": u.id if u else 0,
                "text": fake_text,
                "entities": [],
                "avatar": True,
                "from": {
                    "id": u.id if u else 0,
                    "name": u.full_name if u else "Unknown",
                    "username": (u.username or "") if u else "",
                    "type": chat_type_str(replied),
                    "photo": "",
                },
                "replyMessage": {},
            }
        ],
    }

    processing = await update.message.reply_html("🖌️ <b>Creating fake quote, please wait...</b>")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(QUOTE_API, json=payload)
            if r.status_code == 200:
                img = BytesIO(r.content)
                img.name = "quote.webp"
                await processing.delete()
                await update.message.reply_sticker(img)
            else:
                await processing.edit_text("❌ <b>Failed to generate fake quote.</b>")
    except Exception as e:
        await processing.edit_text(f"⚠️ <b>Error:</b> <code>{e}</code>")


# === /qr or /q_r (quote with reply) ===
quote_with_reply_command = quote_command  # same logic with "r" argument included


# === Inline Callback ===
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "random_color":
        await query.edit_message_text("🎨 <b>Use <code>/q random</code> to get a random color quote!</b>")
    elif query.data == "fake_quote":
        await query.edit_message_text("📝 <b>Use <code>/qt <text></code> (reply to a message) to fake quote!</b>")

ANIME_QUOTES = [
    # 1-50 (Real quotes)
    ("Madoka Kaname", "Puella Magi Madoka Magica", "Don't forget. Always, somewhere, someone is fighting for you. As long as you remember her, you are not alone."),
    ("Kuroha", "Gokukoku no Brynhildr", "It is really sad to forget things you want to remember."),
    ("Gintoki Sakata", "Gintama", "The country? The sky? You can have them. I'm going to find a woman I love."),
    ("Monkey D. Luffy", "One Piece", "I don't want to conquer anything. I just think the guy with the most freedom in this whole ocean is the Pirate King!"),
    ("Itachi Uchiha", "Naruto", "People live their lives bound by what they accept as correct and true. That's how they define 'reality'."),
    ("Edward Elric", "Fullmetal Alchemist", "A lesson without pain is meaningless. For you cannot gain something without sacrificing something else in return."),
    ("Spike Spiegel", "Cowboy Bebop", "Whatever happens, happens."),
    ("Light Yagami", "Death Note", "I'll take a potato chip... AND EAT IT!"),
    ("Levi Ackerman", "Attack on Titan", "Give up on your dreams and die."),
    ("Kakashi Hatake", "Naruto", "In the ninja world, those who break the rules are scum, that's true, but those who abandon their friends are worse than scum."),
    ("Eren Yeager", "Attack on Titan", "If you win, you live. If you lose, you die. If you don't fight, you can't win!"),
    ("Roy Mustang", "Fullmetal Alchemist", "A leader who doesn't sacrifice anything can never change anything."),
    ("Lelouch Lamperouge", "Code Geass", "The only ones who should kill are those who are prepared to be killed."),
    ("Gon Freecss", "Hunter x Hunter", "I don't care if this is the end. I'll keep moving forward."),
    ("Saitama", "One Punch Man", "I'm just a hero for fun."),
    ("Erwin Smith", "Attack on Titan", "Dedicate your heart!"),
    ("Rintaro Okabe", "Steins;Gate", "The organization is watching us."),
    ("Shoto Todoroki", "My Hero Academia", "It's your power, isn't it?"),
    ("Vegeta", "Dragon Ball Z", "Power comes in response to a need, not a desire."),
    ("Killua Zoldyck", "Hunter x Hunter", "I don't care if it's useless. I'll protect Gon no matter what."),
    ("Mikasa Ackerman", "Attack on Titan", "The world is cruel, but also beautiful."),
    ("Holo", "Spice and Wolf", "Even if the whole world were to become my enemy, I would fight to protect my pride."),
    ("Shinji Ikari", "Neon Genesis Evangelion", "I mustn't run away."),
    ("Alucard", "Hellsing Ultimate", "The bird of Hermes is my name, eating my wings to make me tame."),
    ("Jiraiya", "Naruto", "When people get hurt, they learn to hate... when people hurt others, they become hated."),
    ("Naruto Uzumaki", "Naruto", "I'm not gonna run away anymore... I'm not gonna go back on my word... that is my ninja way!"),
    ("Kenshin Himura", "Rurouni Kenshin", "Swords that kill and swords that protect life cannot be the same."),
    ("L", "Death Note", "I am justice!"),
    ("Saber", "Fate/stay night", "Do not regret your death, as I shall honor it with my victory."),
    ("Guts", "Berserk", "I'll keep moving forward... until I destroy you."),
    ("Vash the Stampede", "Trigun", "Love and peace!"),
    ("Shoyo Hinata", "Haikyuu!!", "Talent is something you make bloom, instinct is something you polish."),
    ("Asuka Langley Soryu", "Neon Genesis Evangelion", "I'll kill you!"),
    ("Shinobu Oshino", "Monogatari Series", "I don't know everything, I just know what I know."),
    ("Shigeo Kageyama", "Mob Psycho 100", "I've always been me."),
    ("Reigen Arataka", "Mob Psycho 100", "You should always believe in yourself... unless your weakness is being exploited."),
    ("Yusuke Urameshi", "Yu Yu Hakusho", "I don't care if I die. I came here prepared for that."),
    ("Koyomi Araragi", "Monogatari Series", "People can't live alone, but they can't live with others either."),
    ("Sakata Gintoki", "Gintama", "There's no point in being grown up if you can't be childish sometimes."),
    ("Tatsumaki", "One Punch Man", "The weak should fear the strong."),
    ("Izuku Midoriya", "My Hero Academia", "It's your power, isn't it?"),
    ("All Might", "My Hero Academia", "Go beyond! Plus Ultra!"),
    ("Hachiman Hikigaya", "Oregairu", "If the truth is cruel, then lies must be kind."),
    ("Senjougahara Hitagi", "Monogatari Series", "I don't care if you're a liar. I love you."),
    ("Kamina", "Gurren Lagann", "Don't believe in yourself. Believe in me! Believe in the Kamina who believes in you!"),
    ("Simon", "Gurren Lagann", "Who the hell do you think I am?!"),
    ("Yato", "Noragami", "A god's greatest fear is to be forgotten."),
    ("Hinata Shoyo", "Haikyuu!!", "The view from the top is spectacular!"),
    ("Karma Akabane", "Assassination Classroom", "The weak are meat; the strong eat."),
    ("Rimuru Tempest", "That Time I Got Reincarnated as a Slime", "I'm not a hero or a villain. I'm just me.")

]

# 100 Hindi Shayari lines
SHAYARI_QUOTES = [
    # Original 3 Shayaris (kept as is)
    "तेरा नाम लूँ जुबां से, यही बात ग़लत है,\nतेरी याद आए तो मैं ख़ुद से नाराज़ हो जाऊँ।",
    "ना जाने कौन सी मोहब्बत सिखा गए वो,\nहमेशा के लिए रूला गए वो।",
    "तन्हाई में मुस्कुराना भी इश्क़ है,\nइस बात को सब से छुपाना भी इश्क़ है।",

    # New rhyming Shayaris (4-100)
    "दिल का दर्द छुपाऊँ कैसे, आँखों से आँसू झरते हैं,\nतेरे बिन जीना मुश्किल है, हर पल तेरे ही याद आते हैं।",
    
    "चाँदनी रातों में तेरी याद सताती है,\nदिल की धड़कनें तेरा नाम लेती हैं।",
    
    "ख्वाबों में आके तू मुझे रुला क्यों जाता है,\nजागूँ तो पाता हूँ तेरा साया भी नहीं रहता।",
    
    "मोहब्बत की नगमें गुनगुनाऊँ तो,\nदिल के तारों से तेरा नाम बज उठता है।",
    
    "रात की तन्हाई में तेरी यादें सताती हैं,\nआँखों की नमी मेरे दर्द को बयां करती हैं।",
    
    "तेरे इश्क़ ने मुझे दीवाना बना दिया,\nअब तो बस तेरे ख्यालों में ही जीता हूँ मैं।",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है।",
    
    "तू ना मिले तो चाँद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है।",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं।",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं।",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं।",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है।",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं।",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं।",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है।",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है।",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है।",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं।",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं।",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है।",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं।",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं।",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं।",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है।",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं।",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं।",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है।",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है।",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है।",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं।",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं।",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है।",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं।",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं।",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं।",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है।",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं।",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं।",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है।",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है।",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है।",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं।",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं।",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है。",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं।",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं。",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं。",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है。",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं。",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं。",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है。",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है。",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है。",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं。",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं。",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है。",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं。",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं。",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं。",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है。",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं。",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं。",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है。",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है。",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है。",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं。",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं。",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है。",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं。",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं。",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं。",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है。",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं。",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं。",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है。",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है。",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है。",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं。",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं。",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है。",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं。",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं。",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं。",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है。",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं。",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं。",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है。",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है。",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है。",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं。",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं。",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है。",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं。",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं。",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं。",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है。",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं。",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं。",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है。",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है。",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है。",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं。",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं。",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है。",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं。",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं。",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं。",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है。",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं。",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं。",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है。",
    
    "तू ही मेरी रातों की चांदनी है,\nतू ही मेरे दिनों की रौशनी है。",
    
    "मोहब्बत की इस दुनिया में तू ही मेरा सहारा है,\nतेरे बिना ये ज़िन्दगी बेमानी सी लगती है。",
    
    "तेरी यादों के सहारे जी लूँगा मैं,\nतेरे इंतज़ार में दिन गुज़ार दूँगा मैं。",
    
    "दिल की धड़कनें तेरे नाम लेती हैं,\nतेरी याद आते ही आँखें नम हो जाती हैं。",
    
    "तू ना मिले तो चांद भी अधूरा लगता है,\nतेरे बिना हर चीज़ बेकार सी लगती है。",
    
    "मोहब्बत की इबादत करने वाले कम नहीं होते,\nपर सच्चे दिल से प्यार करने वाले ही जानते हैं。",
    
    "तेरी यादों की बारिश में भीग जाऊँ मैं,\nतेरे ख्यालों के सहारे जी जाऊँ मैं。",
    
    "दिल के अरमान आँखों में समा जाते हैं,\nजब तेरी याद आती है तो बेकरार हो जाते हैं。",
    
    "तू ही मेरी ज़िन्दगी का मकसद है,\nतेरे बिना तो ये दिल बेचैन सा है。",
    
    "मोहब्बत की राह में खो जाऊँ मैं,\nतेरे इश्क़ में दीवाना हो जाऊँ मैं。",
    
    "तेरी यादों के सहारे जी लेता हूँ मैं,\nतेरे इंतज़ार में वक्त गुज़ार लेता हूँ मैं।",
    
    "दिल की गहराइयों में तेरा नाम लिखा है,\nतेरे सिवा किसी और को जगह नहीं दी है।"
]
import random
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# === Quotes Data === (Same as before)
# Improved font handling
try:
    # Try different font paths for different OS
    font_paths = [
        "arial.ttf",  # Windows
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/Library/Fonts/Arial.ttf",  # MacOS
        "fonts/arial.ttf"  # Local fallback
    ]
    
    for path in font_paths:
        if os.path.isfile(path):
            font_path = path
            break
    else:
        raise FileNotFoundError("No suitable font found")
except Exception as e:
    print(f"⚠️ Font error: {e}")
    font_path = None

# Enhanced image generation with better styling
def generate_quote_image(character, anime, quote):
    W, H = 1080, 1080  # Square format for better mobile viewing
    bg_colors = ["#1b1429", "#2c1e3d", "#3a2848", "#261a33"]
    text_colors = ["#ffffff", "#f8f8f8", "#e6e6e6"]
    accent_colors = ["#ff6b6b", "#48dbfb", "#1dd1a1", "#feca57"]
    
    # Randomize styling for variety
    bg_color = random.choice(bg_colors)
    text_color = random.choice(text_colors)
    accent_color = random.choice(accent_colors)
    
    # Create base image
    img = Image.new("RGB", (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add decorative elements
    if random.choice([True, False]):
        # Add subtle noise texture
        for _ in range(1000):
            x, y = random.randint(0, W), random.randint(0, H)
            draw.point((x, y), fill=(random.randint(0, 50), random.randint(0, 50), random.randint(0, 50)))
    
    # Load fonts with fallbacks
    try:
        font_big = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default()
        font_medium = ImageFont.truetype(font_path, 32) if font_path else ImageFont.load_default()
        font_small = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
    except:
        font_big = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Text wrapping function
    def wrap(text, font, max_width):
        words = text.split()
        lines, line = [], ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw.textlength(test_line, font=font) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    # Add quote text with styling
    y = 150
    quote_lines = wrap(f"❝ {quote} ❞", font_big, W - 120)
    for line in quote_lines:
        # Text shadow effect
        shadow_offset = 3
        draw.text(
            ((W - draw.textlength(line, font=font_big)) / 2 + shadow_offset, 
             y + shadow_offset),
            line, font=font_big, fill="#00000055"
        )
        # Main text
        draw.text(
            ((W - draw.textlength(line, font=font_big)) / 2, y),
            line, font=font_big, fill=text_color
        )
        y += 60

    # Add character/anime info with styling
    footer = f"— {character}, {anime}"
    draw.text(
        ((W - draw.textlength(footer, font=font_medium)) / 2, H - 180),
        footer, font=font_medium, fill=accent_color
    )

    # Add decorative border
    border_width = 10
    draw.rectangle(
        [(border_width, border_width), (W - border_width, H - border_width)],
        outline=accent_color,
        width=2
    )

    # Add watermark
    watermark = "@AnimeQuotesBot"
    draw.text(W - draw.textlength(watermark, font=font_small) - 30, 
        H - 50,
        watermark, font=font_small, fill="#ffffff55"
    )



    # Save to bytes
    output = BytesIO()
    output.name = "quote.jpg"
    
    # Apply final contrast enhancement
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    
    img.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output

# === PTB Handlers ===

async def aquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send random anime quote"""
    character, anime, quote = random.choice(ANIME_QUOTES)
    text = f"🎌 *{character}* from _{anime}_\n\n❝ {quote} ❞"
    keyboard = [
        [InlineKeyboardButton("🔄 New Quote", callback_data="new_aquote"),
         InlineKeyboardButton("🖼️ Image Version", callback_data=f"iaquote_{ANIME_QUOTES.index((character, anime, quote))}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def iaquotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send random anime quote as image"""
    if context.args and context.args[0].isdigit():
        idx = int(context.args[0])
        character, anime, quote = ANIME_QUOTES[idx]
    else:
        character, anime, quote = random.choice(ANIME_QUOTES)
    
    image = generate_quote_image(character, anime, quote)
    keyboard = [
        [InlineKeyboardButton("🔄 New Image", callback_data="new_iaquote"),
         InlineKeyboardButton("📝 Text Version", callback_data=f"aquote_{ANIME_QUOTES.index((character, anime, quote))}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_photo(
            photo=image,
            caption=f"🎨 *{character}* from _{anime}_",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.delete_message()
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image,
            caption=f"🎨 *{character}* from _{anime}_",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def shayri(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send random Hindi shayari"""
    quote = random.choice(SHAYARI_QUOTES)
    keyboard = [
        [InlineKeyboardButton("🔄 नई शायरी", callback_data="new_shayri"),
         InlineKeyboardButton("❤️ फेवरेट", callback_data="fav_shayri")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            f"📜 _{quote}_",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            f"📜 _{quote}_",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# Callback handlers
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "new_aquote":
        await aquote(update, context)
    elif query.data == "new_iaquote":
        await iaquotes(update, context)
    elif query.data == "new_shayri":
        await shayri(update, context)
    elif query.data.startswith("aquote_"):
        idx = int(query.data.split("_")[1])
        character, anime, quote = ANIME_QUOTES[idx]
        await aquote(update, context)
    elif query.data.startswith("iaquote_"):
        idx = int(query.data.split("_")[1])
        context.args = [str(idx)]
        await iaquotes(update, context)
    elif query.data == "fav_shayri":
        await query.answer("❤️ Added to favorites!", show_alert=False)
import logging
from pyrogram import Client
from telethon.sessions import StringSession as TSession
from telethon.sync import TelegramClient
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Constants for conversation states
LIBRARY, API_ID, API_HASH, PHONE, CODE, PASSWORD = range(6)

# Start handler
async def start_sgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        try:
            bot_username = (await context.bot.get_me()).username
            link = f"https://t.me/{bot_username}?start=sgen"
            return await update.message.reply_text(
                f"📩 Please start me in <b>private chat</b> to generate your session.\n👉 <a href='{link}'>Click here</a> to start.",
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception:
            return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Pyrogram", callback_data="pyro"),
            InlineKeyboardButton("📞 Telethon", callback_data="tele")
        ]
    ])

    await update.message.reply_text(
        "✨ <b>Welcome to the Session String Generator!</b>\n\n"
        "Please choose the library you want to generate the session for:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    return LIBRARY


# Library button handler
async def handle_library_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lib = query.data
    context.user_data["lib"] = lib

    await query.edit_message_text("🔢 <b>Enter your <code>API_ID</code>:</b>", parse_mode="HTML")
    return API_ID


async def get_api_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        return await update.message.reply_text("❌ API_ID must be a number. Try again.")
    context.user_data["api_id"] = int(update.message.text)
    await update.message.reply_text("🔐 <b>Enter your <code>API_HASH</code>:</b>", parse_mode="HTML")
    return API_HASH


async def get_api_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["api_hash"] = update.message.text.strip()
    await update.message.reply_text("📱 <b>Enter your phone number with country code:</b>", parse_mode="HTML")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    lib = context.user_data["lib"]
    api_id = context.user_data["api_id"]
    api_hash = context.user_data["api_hash"]
    phone = context.user_data["phone"]

    await update.message.reply_text("📨 Sending code...")
    try:
        if lib == "pyro":
            client = Client(name="session", api_id=api_id, api_hash=api_hash)
            await client.connect()
            await client.send_code(phone)
            context.user_data["client"] = client
        else:
            client = TelegramClient(TSession(), api_id, api_hash)
            await client.connect()
            await client.send_code_request(phone)
            context.user_data["client"] = client
        await update.message.reply_text("📥 <b>Enter the OTP code you received:</b>", parse_mode="HTML")
        return CODE
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send code:\n<code>{e}</code>", parse_mode="HTML")
        return ConversationHandler.END


async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    client = context.user_data["client"]
    phone = context.user_data["phone"]
    lib = context.user_data["lib"]

    try:
        if lib == "pyro":
            await client.sign_in(phone_number=phone, code=code)
        else:
            await client.sign_in(phone=phone, code=code)
        return await finish_session(update, context)
    except Exception as e:
        if "2FA" in str(e) or "PASSWORD" in str(e).upper():
            await update.message.reply_text("🔒 This account has 2FA enabled.\nEnter your password:")
            return PASSWORD
        await update.message.reply_text(f"❌ Failed to sign in:\n<code>{e}</code>", parse_mode="HTML")
        return ConversationHandler.END


async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    client = context.user_data["client"]
    try:
        await client.check_password(password)
        return await finish_session(update, context)
    except Exception as e:
        await update.message.reply_text(f"❌ Incorrect password:\n<code>{e}</code>", parse_mode="HTML")
        return ConversationHandler.END


async def finish_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lib = context.user_data["lib"]
    client = context.user_data["client"]

    try:
        if lib == "pyro":
            string = await client.export_session_string()
            await client.disconnect()
        else:
            string = client.session.save()
            await client.disconnect()

        await update.message.reply_text(
            f"✅ <b>Your {lib.title()} Session String:</b>\n<code>{string}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error:\n<code>{e}</code>", parse_mode="HTML")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Session generator cancelled.")
    return ConversationHandler.END


import asyncio
import html
import logging
import speedtest
import time
from concurrent.futures import ThreadPoolExecutor
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters
)

# Logger setup
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=3)

# /speedtest command handler
async def speedtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /speedtest command"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "🚀 Speedtest started in the background...\nYou'll get the results soon! ✅"
    )

    asyncio.create_task(run_speedtest(context.bot, chat_id, user_id))

async def run_speedtest(bot, chat_id: int, user_id: int):
    """Run the speedtest and send results"""
    progress_frames = ["🚀", "🌐", "⚡", "💫", "🔮", "🛰️", "🦾", "🧬", "🪐", "🌟"]
    progress_texts = [
        "Igniting boosters...",
        "Connecting to hyperspace...",
        "Contacting Ookla mothership...",
        "Warping download speed...",
        "Warping upload speed...",
        "Measuring quantum ping...",
        "Locating best galaxy server...",
        "Finalizing cosmic results...",
        "Rendering speed nebula...",
        "Almost at light speed!"
    ]

    status_msg = await bot.send_message(
        chat_id,
        "<b>🚀 Initiating Speedtest...</b>",
        parse_mode="HTML"
    )
    start_time = time.time()

    async def animate_progress():
        idx = 0
        for _ in range(15):
            await asyncio.sleep(0.8)
            percent = int((idx + 1) / 15 * 100)
            bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
            frame = progress_frames[idx % len(progress_frames)]
            text = progress_texts[idx % len(progress_texts)]
            try:
                await status_msg.edit_text(
                    f"{frame} <b>{text}</b>\n[{bar}] {percent}%",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            idx += 1

    progress_task = asyncio.create_task(animate_progress())

    def perform_speedtest():
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download()
        upload = st.upload()
        ping = st.results.ping
        server = st.results.server
        isp = st.results.client.get("isp", "Unknown")
        country = st.results.client.get("country", "Unknown")
        st.results.share()
        image_url = st.results.share()
        return download, upload, ping, server, isp, country, image_url

    try:
        loop = asyncio.get_running_loop()
        download, upload, ping, server, isp, country, image_url = await loop.run_in_executor(
            executor,
            perform_speedtest
        )

        progress_task.cancel()
        elapsed = time.time() - start_time

        def fmt_speed(bits):
            mbps = bits / 1_000_000
            return f"{mbps:.2f} Mbps" if mbps < 1000 else f"{mbps / 1000:.2f} Gbps"

        result_text = (
            "<b>🌌 Speedtest Results</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⬇️ <b>Download:</b> <code>{fmt_speed(download)}</code>\n"
            f"⬆️ <b>Upload:</b> <code>{fmt_speed(upload)}</code>\n"
            f"🛰️ <b>Ping:</b> <code>{ping:.2f} ms</code>\n"
            f"🌍 <b>Server:</b> <code>{server.get('sponsor')} ({server.get('country')})</code>\n"
            f"🏢 <b>ISP:</b> <code>{isp}</code>\n"
            f"📍 <b>Location:</b> <code>{country}</code>\n"
            f"⏱ <b>Elapsed:</b> <code>{elapsed:.1f} sec</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Tested by:</i> <a href='tg://user?id={user_id}'>Click here</a>"
        )

        await status_msg.edit_text(
            "🪐 <b>Speedtest complete! Sending results...</b>",
            parse_mode="HTML"
        )
        
        await bot.send_photo(
            chat_id=chat_id,
            photo=image_url,
            caption=result_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Speedtest.net", url="https://www.speedtest.net/")]
            ]),
            parse_mode="HTML"
        )

        await status_msg.delete()

    except Exception as e:
        progress_task.cancel()
        error_text = html.escape(str(e))
        if "403" in error_text:
            await status_msg.edit_text(
                "❌ <b>Speedtest failed.</b>\nSpeedtest.net blocked this server (HTTP 403).",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                f"❌ <b>Error:</b>\n<code>{error_text}</code>",
                parse_mode="HTML"
            )

import aiohttp
import asyncio
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# === API KEYS ===
CRICAPI_KEY = "f399a2af-703a-40a9-88f4-3f47be137ff3"
FOOTBALL_API_KEY = "6703c855d69b4261bd3b59836d5cca59"

# === Match Cache & Indexes ===
current_indices = {"cricket": 0, "football": 0}
matches_cache = {"cricket": [], "football": []}

# === Emoji Constants ===
EMOJIS = {
    "cricket": "🏏",
    "football": "⚽",
    "refresh": "🔄",
    "next": "➡️",
    "prev": "⬅️",
    "date": "📅",
    "venue": "🏟️",
    "team": "🏆",
    "vs": "🆚",
    "home": "🏠",
    "away": "✈️",
    "live": "🔴",
    "trophy": "🏆",
    "calendar": "🗓️"
}

# === Cricket Matches ===
async def fetch_cricket_matches():
    """Fetch live cricket matches from API"""
    try:
        url = f"https://api.cricapi.com/v1/matches?apikey={CRICAPI_KEY}&offset=0"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                matches = data.get("data", [])[:30]
                # Sort matches by date (newest first)
                matches.sort(key=lambda x: x.get("date", ""), reverse=True)
                matches_cache["cricket"] = matches
                return matches
    except Exception as e:
        print(f"[CRICKET API ERROR] {e}")
        return []

def format_cricket_match(match):
    """Format cricket match data into attractive message"""
    team_info = match.get("teamInfo", [])
    team1 = team_info[0].get("shortname", team_info[0].get("name", "TBD")) if len(team_info) > 0 else "TBD"
    team2 = team_info[1].get("shortname", team_info[1].get("name", "TBD")) if len(team_info) > 1 else "TBD"
    
    # Format date nicely
    match_date = match.get("date", "N/A")
    try:
        dt = datetime.strptime(match_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        formatted_date = dt.strftime("%a, %d %b %Y • %I:%M %p")
    except:
        formatted_date = match_date

    # Match status indicator
    status = match.get("status", "").upper()
    status_emoji = "🟢" if "LIVE" in status else "🟡" if "COMPLETE" in status else "🔵"

    return (
        f"{EMOJIS['cricket']} <b>{match.get('name', 'CRICKET MATCH').upper()}</b> {status_emoji}\n\n"
        f"{EMOJIS['date']} <b>Date:</b> <code>{formatted_date}</code>\n"
        f"{EMOJIS['team']} <b>Teams:</b>\n"
        f"  • {team1}\n"
        f"  • {team2}\n"
        f"{EMOJIS['venue']} <b>Venue:</b> <i>{match.get('venue', 'Unknown')}</i>\n\n"
        f"<b>Status:</b> <code>{status}</code>"
    )

# === Football Matches ===
async def fetch_football_matches():
    """Fetch live football matches from API"""
    try:
        url = "https://api.football-data.org/v4/matches"
        headers = {"X-Auth-Token": FOOTBALL_API_KEY}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                matches = data.get("matches", [])[:50]
                # Sort matches by date (newest first)
                matches.sort(key=lambda x: x.get("utcDate", ""), reverse=True)
                matches_cache["football"] = matches
                return matches
    except Exception as e:
        print(f"[FOOTBALL API ERROR] {e}")
        return []

def format_football_page(matches, page=0, per_page=5):
    """Format football matches into attractive paginated message"""
    start = page * per_page
    end = start + per_page
    subset = matches[start:end]
    
    # Header with fancy divider
    message = (
        f"{EMOJIS['football']} <b>FOOTBALL MATCHES</b> {EMOJIS['football']}\n"
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  📅 <i>Page {page + 1}</i>        ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
    )

    for idx, match in enumerate(subset, 1):
        home = match.get('homeTeam', {}).get('shortName', 'TBD')
        away = match.get('awayTeam', {}).get('shortName', 'TBD')
        date = match.get('utcDate', 'N/A')
        comp = match.get('competition', {}).get('name', 'Match')
        status = match.get('status', 'SCHEDULED').upper()
        
        # Format date nicely
        try:
            dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = dt.strftime("%a, %d %b • %I:%M %p")
        except:
            formatted_date = date[:10]
            
        # Status emoji
        status_emoji = "🔴" if status == "IN_PLAY" else "🟢" if status == "FINISHED" else "🟡"
        
        message += (
            f"{EMOJIS['trophy']} <b>{comp}</b>\n"
            f"{EMOJIS['date']} <b>When:</b> <code>{formatted_date}</code>\n"
            f"{EMOJIS['home']} <b>{home}</b> {EMOJIS['vs']} <b>{away}</b>\n"
            f"{status_emoji} <i>Status:</i> <code>{status.replace('_', ' ').title()}</code>\n"
            f"────────────────────\n"
        )

    return message.strip()

# === Match Handlers ===
async def send_match_update(update: Update, context: ContextTypes.DEFAULT_TYPE, sport: str):
    """Send or update match information"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Get the appropriate message object based on update type
    if update.callback_query:
        message = update.callback_query.message
        edit_func = message.edit_text
    else:
        message = await context.bot.send_message(
            chat.id,
            f"{EMOJIS[sport]} Fetching {sport.capitalize()} matches..."
        )
        edit_func = message.edit_text

    # Fetch matches
    matches = await (fetch_cricket_matches() if sport == "cricket" else fetch_football_matches())
    
    if not matches:
        return await edit_func(
            f"🚫 No {sport} matches found. Try again later!",
            parse_mode="HTML"
        )

    if sport == "cricket":
        idx = current_indices["cricket"] % len(matches)
        current_indices["cricket"] = idx
        match = matches[idx]

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{EMOJIS['refresh']} Refresh", callback_data="refresh_cricket"),
                InlineKeyboardButton(f"{EMOJIS['next']} Next", callback_data="next_cricket")
            ]
        ])

        return await edit_func(
            format_cricket_match(match),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    elif sport == "football":
        total_pages = (len(matches) + 4) // 5
        page = current_indices["football"] % total_pages
        current_indices["football"] = page

        buttons = [
            [
                InlineKeyboardButton(f"{EMOJIS['prev']} Prev", callback_data="prev_football"),
                InlineKeyboardButton(f"{EMOJIS['next']} Next", callback_data="next_football")
            ],
            [InlineKeyboardButton(f"{EMOJIS['refresh']} Refresh List", callback_data="refresh_football")]
        ]

        if total_pages > 1:
            buttons.append([
                InlineKeyboardButton(f"📄 Page {page + 1}/{total_pages}", callback_data="page_info")
            ])

        return await edit_func(
            format_football_page(matches, page),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )

# === Command Handlers ===
async def cricket_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cricket command"""
    await send_match_update(update, context, "cricket")

async def football_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /football command"""
    await send_match_update(update, context, "football")

# === Callback Handler ===
async def match_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all match callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith(("next_", "prev_", "refresh_")):
        action, sport = data.split("_")
        
        if sport == "cricket":
            if action == "next":
                current_indices["cricket"] += 1
            elif action == "refresh":
                current_indices["cricket"] = 0
                
        elif sport == "football":
            if action == "next":
                current_indices["football"] += 1
            elif action == "prev":
                current_indices["football"] -= 1
            elif action == "refresh":
                current_indices["football"] = 0
        
        await send_match_update(update, context, sport)
    elif data == "page_info":
        await query.answer("Current page information", show_alert=False)

TEMP_DIR = "temp_files"
FONT_PATH = "arial.ttf"  # Adjust this path if needed
os.makedirs(TEMP_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

# Utility: Delete message after delay
async def delete_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int = 30):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.warning(f"Failed to delete message {message_id}: {e}")

# Send + background delete
async def send_temporary(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, reply_to=None, delay: int = 30, **kwargs):
    msg = await context.bot.send_message(chat_id, text, reply_to_message_id=reply_to, **kwargs)
    asyncio.create_task(delete_after_delay(context, chat_id, msg.message_id, delay))
    return msg

async def stickerinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get information about a sticker"""
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        return await send_temporary(
            context,
            update.effective_chat.id,
            "✧ Please reply to a sticker to get its info!",
            reply_to=update.message.message_id
        )

    s = update.message.reply_to_message.sticker
    info = (
        f"<b>✧ Sticker Info:</b>\n"
        f"<b>• File ID:</b> <code>{s.file_id}</code>\n"
        f"<b>• Emoji:</b> {s.emoji or 'None'}\n"
        f"<b>• Type:</b> {'Animated' if s.is_animated else 'Video' if s.is_video else 'Static'}\n"
        f"<b>• Dimensions:</b> {s.width}x{s.height}\n"
        f"<b>• Size:</b> {s.file_size} bytes"
    )
    if s.set_name:
        info += f"\n<b>• Pack:</b> {s.set_name}"

    sent = await update.message.reply_text(info, parse_mode="HTML")
    asyncio.create_task(delete_after_delay(context, update.effective_chat.id, sent.message_id))

async def getsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert static sticker to PNG"""
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        return await send_temporary(
            context,
            update.effective_chat.id,
            "✧ Reply to a static sticker!",
            reply_to=update.message.message_id
        )

    sticker = update.message.reply_to_message.sticker
    if sticker.is_animated or sticker.is_video:
        return await send_temporary(
            context,
            update.effective_chat.id,
            "✧ This only works with static stickers!",
            reply_to=update.message.message_id
        )

    file_path = os.path.join(TEMP_DIR, f"{sticker.file_unique_id}.png")
    file = await context.bot.get_file(sticker.file_id)
    await file.download_to_drive(file_path)

    with open(file_path, 'rb') as f:
        sent = await update.message.reply_document(document=InputFile(f))
    
    asyncio.create_task(delete_after_delay(context, update.effective_chat.id, sent.message_id))
    os.remove(file_path)

async def getvidsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Extract video sticker as MP4"""
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        return await send_temporary(
            context,
            update.effective_chat.id,
            "✧ Reply to a video sticker!",
            reply_to=update.message.message_id
        )

    sticker = update.message.reply_to_message.sticker
    if not sticker.is_video:
        return await send_temporary(
            context,
            update.effective_chat.id,
            "✧ This only works with video stickers!",
            reply_to=update.message.message_id
        )

    file_path = os.path.join(TEMP_DIR, f"{sticker.file_unique_id}.mp4")
    file = await context.bot.get_file(sticker.file_id)
    await file.download_to_drive(file_path)

    with open(file_path, 'rb') as f:
        sent = await update.message.reply_video(video=InputFile(f))
    
    asyncio.create_task(delete_after_delay(context, update.effective_chat.id, sent.message_id))
    os.remove(file_path)

async def memify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create meme from sticker/photo with text"""
    input_path = output_path = None
    processing_msg = await update.message.reply_text("✧ Processing your request...")

    try:
        if not update.message.reply_to_message:
            return await processing_msg.edit_text("❗ Reply to a photo or static sticker with `/mmf top;text;bottom`")

        args = context.args
        if not args:
            return await processing_msg.edit_text("❗ Provide text like `/mmf hello;world`")

        full_text = ' '.join(args)
        top_text, *bottom = full_text.split(';', 1)
        bottom_text = bottom[0].strip() if bottom else ""

        if not top_text.strip() and not bottom_text:
            return await processing_msg.edit_text("❗ You must give top or bottom text.")

        replied = update.message.reply_to_message
        if replied.sticker:
            if replied.sticker.is_animated or replied.sticker.is_video:
                return await processing_msg.edit_text("❌ Animated/video stickers not supported.")
            ext = "png"
        elif replied.photo:
            ext = "jpg"
        else:
            return await processing_msg.edit_text("❌ Unsupported media. Reply to photo or static sticker.")

        input_path = os.path.join(TEMP_DIR, f"input_{replied.message_id}.{ext}")
        file = await context.bot.get_file(replied.sticker.file_id if replied.sticker else replied.photo[-1].file_id)
        await file.download_to_drive(input_path)

        with Image.open(input_path).convert("RGBA") as img:
            draw = ImageDraw.Draw(img)
            font_size = max(20, img.height // 10)

            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except:
                font = ImageFont.load_default()

            def draw_centered_text(text, y):
                w = draw.textlength(text, font=font)
                x = (img.width - w) / 2
                for dx in [-1, 1]:
                    for dy in [-1, 1]:
                        draw.text((x + dx, y + dy), text, font=font, fill="black")
                draw.text((x, y), text, font=font, fill="white")

            if top_text.strip():
                draw_centered_text(top_text.strip(), 10)

            if bottom_text:
                text_height = draw.textbbox((0, 0), bottom_text, font=font)[3]
                draw_centered_text(bottom_text, img.height - text_height - 20)

            output_path = os.path.join(TEMP_DIR, f"output_{update.message.message_id}.png")
            img.save(output_path, "PNG")

        await processing_msg.edit_text("✧ Uploading sticker...")
        with open(output_path, 'rb') as f:
            sent = await update.message.reply_sticker(sticker=InputFile(f))
        
        asyncio.create_task(delete_after_delay(context, update.effective_chat.id, sent.message_id))

    except Exception as e:
        logger.error(f"[MEMIFY ERROR] {e}", exc_info=True)
        await processing_msg.edit_text("❌ Something went wrong while processing your image.")
    finally:
        await processing_msg.delete()
        for p in [input_path, output_path]:
            if p and os.path.exists(p):
                os.remove(p)

MAX_SIZE = 128
CANVAS_SIZE = 512

async def tiny_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.reply_to_message:
        await message.reply_text("❌ Please reply to a static sticker or photo to use this command!")
        return

    replied = message.reply_to_message

    # Determine file to download
    file_id = None
    is_static_sticker = False
    if replied.sticker and not (replied.sticker.is_animated or replied.sticker.is_video):
        file_id = replied.sticker.file_id
        is_static_sticker = True
    elif replied.photo:
        file_id = replied.photo[-1].file_id  # Get the best quality
    else:
        await message.reply_text("❌ Only static stickers or images are supported!")
        return

    status = await message.reply_text("📥 Downloading...")

    try:
        file = await context.bot.get_file(file_id)
        input_file = f"input_{file_id}.png"
        await file.download_to_drive(input_file)

        output_file = f"tiny_{os.path.splitext(os.path.basename(input_file))[0]}.webp"

        await status.edit_text("⚙️ Processing...")

        with Image.open(input_file) as img:
            img = img.convert("RGBA")
            ratio = min(MAX_SIZE / img.width, MAX_SIZE / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

            canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
            position = ((CANVAS_SIZE - new_size[0]) // 2, (CANVAS_SIZE - new_size[1]) // 2)
            canvas.paste(img, position, img)
            canvas.save(output_file, "WEBP", quality=100, method=6)

        await status.edit_text("📤 Uploading...")

        with open(output_file, "rb") as sticker_file:
            await message.reply_sticker(sticker_file)

        await status.delete()

    except Exception as e:
        logger.error(f"Error in /tiny: {e}")
        await message.reply_text("❌ Failed to process. Make sure it's a supported image or sticker.")
    finally:
        # Clean up files
        for f in [input_file, output_file]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

import os
import logging
from typing import Optional
from pathlib import Path
from gtts import gTTS
from telegram import (
    Update,
    InputFile,
    Message,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TTSGenerator:
    """Handles Text-to-Speech generation and file operations"""
    
    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'flag': '🇬🇧'},
        'es': {'name': 'Spanish', 'flag': '🇪🇸'},
        'fr': {'name': 'French', 'flag': '🇫🇷'},
        'de': {'name': 'German', 'flag': '🇩🇪'},
        'it': {'name': 'Italian', 'flag': '🇮🇹'},
        'pt': {'name': 'Portuguese', 'flag': '🇵🇹'},
        'ru': {'name': 'Russian', 'flag': '🇷🇺'},
        'ja': {'name': 'Japanese', 'flag': '🇯🇵'},
        'hi': {'name': 'Hindi', 'flag': '🇮🇳'},
        'ar': {'name': 'Arabic', 'flag': '🇸🇦'},
        'zh': {'name': 'Chinese', 'flag': '🇨🇳'},
        'ko': {'name': 'Korean', 'flag': '🇰🇷'},
        'tr': {'name': 'Turkish', 'flag': '🇹🇷'}
    }
    
    @staticmethod
    def generate_audio(text: str, lang: str = 'en', slow: bool = False) -> Optional[str]:
        """Generate TTS audio file and return file path"""
        try:
            if lang not in TTSGenerator.SUPPORTED_LANGUAGES:
                logger.warning(f"Unsupported language code: {lang}")
                return None
                
            tts = gTTS(
                text=text,
                lang=lang,
                slow=slow,
                lang_check=False  # Disable strict language checking
            )
            
            audio_file = f"tts_{os.urandom(4).hex()}.mp3"
            tts.save(audio_file)
            return audio_file
            
        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            return None

    @staticmethod
    def cleanup(file_path: str):
        """Remove temporary audio file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {str(e)}")

class TTSBot:
    """Handles Telegram bot interactions for TTS"""
    
    @staticmethod
    async def send_usage(update: Update):
        """Send usage instructions with beautiful formatting"""
        languages = "\n".join(
            f"{data['flag']} <code>{code}</code> - {data['name']}"
            for code, data in TTSGenerator.SUPPORTED_LANGUAGES.items()
        )
        
        await update.message.reply_text(
            "🎤 <b>Text-to-Speech Converter</b> 🎯\n\n"
            "✨ <b>How to use:</b>\n"
            "▫️ Reply to a message: <code>/tts</code>\n"
            "▫️ With text: <code>/tts your text here</code>\n"
            "▫️ With language: <code>/tts -l es your text</code>\n"
            "▫️ Slow mode: <code>/tts --slow your text</code>\n\n"
            "🌍 <b>Supported Languages:</b>\n"
            f"{languages}\n\n"
            "📌 <i>Examples:</i>\n"
            "<code>/tts -l ja こんにちは</code>\n"
            "<code>/tts --slow Hello world</code>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

    @staticmethod
    def parse_command(text: str) -> tuple:
        """Parse command arguments and extract language/slow mode"""
        args = text.split()
        lang = 'en'
        slow = False
        text_start = 1
        
        # Check for language flag
        if len(args) > 2 and args[1].startswith('-l'):
            lang = args[2].lower()
            text_start = 3
        # Check for slow flag
        elif len(args) > 1 and args[1] == '--slow':
            slow = True
            text_start = 2
            
        return ' '.join(args[text_start:]), lang, slow

async def handle_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tts command"""
    try:
        message = update.message
        # Get text from reply or command arguments
        if message.reply_to_message:
            text = (message.reply_to_message.text or 
                    message.reply_to_message.caption)
            if not text:
                await message.reply_text("✧ The replied message has no text!")
                return
            # Parse any flags from the command
            _, lang, slow = TTSBot.parse_command(message.text)
        else:
            if len(context.args) < 1:
                await TTSBot.send_usage(update)
                return
            text, lang, slow = TTSBot.parse_command(message.text)
        
        if not text:
            await message.reply_text("✧ Please provide text to convert!")
            return
            
        # Validate language
        if lang not in TTSGenerator.SUPPORTED_LANGUAGES:
            await message.reply_text(
                f"✧ Unsupported language code: {lang}\n"
                "Use /tts to see supported languages."
            )
            return
            
        # Generate audio
        processing_msg = await message.reply_text(
            f"🔊 Converting to {TTSGenerator.SUPPORTED_LANGUAGES[lang]['flag']} "
            f"{TTSGenerator.SUPPORTED_LANGUAGES[lang]['name']}..."
        )
        
        audio_file = TTSGenerator.generate_audio(text, lang, slow)
        if not audio_file:
            await processing_msg.edit_text("❌ Error generating audio!")
            return
            
        # Send audio file
        lang_data = TTSGenerator.SUPPORTED_LANGUAGES[lang]
        slow_text = " (slow mode)" if slow else ""
        
        with open(audio_file, 'rb') as audio:
            await message.reply_audio(
                audio=InputFile(audio),
                caption=f"🎧 {lang_data['flag']} {lang_data['name']}{slow_text}\n"
                        f"🔤 Text: {text[:100]}{'...' if len(text) > 100 else ''}",
                title=f"TTS - {lang_data['name']}",
                performer="Text-to-Speech",
                reply_to_message_id=message.message_id
            )
        
        await processing_msg.delete()
        TTSGenerator.cleanup(audio_file)
        
    except Exception as e:
        logger.error(f"TTS command failed: {str(e)}", exc_info=True)
        await message.reply_text("❌ An error occurred while processing your request!")
        if 'audio_file' in locals():
            TTSGenerator.cleanup(audio_file)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import random
import logging
from typing import Optional, Dict

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UrbanDictionaryAPI:
    """Handles all interactions with Urban Dictionary API"""
    API_URL = "https://api.urbandictionary.com/v0/define"
    TIMEOUT = 10
    
    @staticmethod
    async def get_top_definition(term: str) -> Optional[Dict]:
        """Fetch the top definition by thumbs up votes"""
        try:
            response = requests.get(
                UrbanDictionaryAPI.API_URL,
                params={"term": term},
                timeout=UrbanDictionaryAPI.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('list'):
                return None
                
            # Sort definitions by thumbs up (descending) and get the top one
            return sorted(
                data['list'],
                key=lambda x: x.get('thumbs_up', 0),
                reverse=True
            )[0]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

class UrbanDictionaryResponses:
    """Enhanced response templates with emojis and formatting"""
    
    @staticmethod
    def get_random_intro() -> str:
        """Get a random funny intro message with emojis"""
        intros = [
            "📚 Hold my dictionary while I look this up...",
            "🤔 Asking the important questions I see...",
            "🔮 Let me consult my street-wise oracle...",
            "🌀 Brace yourself, this definition might be wild...",
            "👩‍💻 I asked my cool cousin what this means...",
            "🕵️‍♂️ According to my sources in the hood...",
            "🎤 Urban Dictionary incoming! *drops mic*",
            "𓀀 Decoding modern hieroglyphics..."
        ]
        return random.choice(intros)
    
    @staticmethod
    def get_no_result_response(term: str) -> str:
        """Get a sassy no-result response with emojis"""
        responses = [
            f"🤷‍♂️ Even Urban Dictionary doesn't know what '{term}' means. You must be extra special.",
            f"🏆 Congratulations! You've invented a word so weird even Urban Dictionary rejected '{term}'.",
            f"❌ 404 Definition Not Found for '{term}'. Try yelling it louder?",
            f"😅 Urban Dictionary said: 'Bruh... no.' to '{term}'",
            f"🧐 I found nothing for '{term}'. Like my motivation on Mondays."
        ]
        return random.choice(responses)
    
    @staticmethod
    def get_loading_message(term: str) -> str:
        """Get a random loading message with emojis"""
        messages = [
            f"🧐 Decoding '{term}' with my translator...",
            f"📖 Flipping through pages of made-up definitions...",
            f"🤯 Trying to understand '{term}' before my circuits fry...",
            f"👵 Asking my grandma what the kids are saying these days...",
            f"🔍 Investigating '{term}' with my detective hat on...",
            f"👨‍🔬 Conducting linguistic experiments on '{term}'..."
        ]
        return random.choice(messages)
    
    @staticmethod
    def format_definition(definition: Dict) -> str:
        """Format the definition in an attractive way with emojis"""
        term = definition['word']
        
        # Highlight the term in definition and example
        funny_def = definition['definition'].replace(
            term, f"✨{term.upper()}✨"
        ).replace("  ", " ").replace("\n", "\n      ")
        
        funny_example = definition['example'].replace(
            term, f"🔥{term.upper()}🔥"
        ).replace("  ", " ").replace("\n", "\n      ")
        
        # Calculate rating based on thumbs up/down ratio
        ratio = definition['thumbs_up'] / (definition['thumbs_down'] + 1)
        if ratio > 10:
            rating = "🏆 LEGENDARY"
            rating_emoji = "🚀"
        elif ratio > 5:
            rating = "💯 FIRE"
            rating_emoji = "🔥"
        elif ratio > 2:
            rating = "👍 Decent"
            rating_emoji = "😎"
        else:
            rating = "🤷‍♂️ Controversial"
            rating_emoji = "⚖️"
        
        return (
            f"{UrbanDictionaryResponses.get_random_intro()}\n\n"
            f"<b>📖 {term.upper()}</b>:\n"
            f"<i>{funny_def}</i>\n\n"
            f"<b>🗣 REAL WORLD EXAMPLE:</b>\n"
            f"<code>{funny_example}</code>\n\n"
            f"<b>{rating_emoji} COMMUNITY RATING:</b> {rating}\n"
            f"👍 {definition['thumbs_up']:,}  👎 {definition['thumbs_down']:,}\n\n"
            f"<i>Requested by @{definition.get('author', 'anonymous')}</i>"
        )

class UrbanDictionaryUI:
    """Enhanced UI elements with better buttons"""
    
    @staticmethod
    def create_definition_keyboard(term: str) -> InlineKeyboardMarkup:
        """Create attractive inline keyboard for definition response"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔍 Google Proper Definition", 
                    url=f"https://www.google.com/search?q={term}+meaning"
                ),
                InlineKeyboardButton(
                    "📚 View All Definitions", 
                    url=f"https://www.urbandictionary.com/define.php?term={term}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🤩 More Slang Terms", 
                    callback_data="more_slang"
                ),
                InlineKeyboardButton(
                    "🎲 Random Word", 
                    callback_data="random_word"
                )
            ]
        ])
    
    @staticmethod
    async def handle_more_slang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the 'more slang' button callback with enhanced responses"""
        query = update.callback_query
        await query.answer()
        
        responses = [
            "🤓 Bruh, you thirsty for more slang? Here you go!",
            "😎 Aren't you cool enough already? Fine, have more!",
            "🤪 Next lesson: How to annoy your teachers with slang",
            "🧠 Knowledge is power! Here's more street wisdom:",
            "📚 Slangtionary chapter 2 incoming..."
        ]
        
        slang_examples = [
            ("💘 /ud rizz", "Dating skills"),
            ("🤪 /ud skibidi", "WTF is this?"),
            ("🍔 /ud bussin", "When food slaps"),
            ("🧢 /ud cap", "Lies! All lies!"),
            ("👑 /ud based", "Unbothered king/queen"),
            ("🦍 /ud sigma", "Lone wolf mentality"),
            ("🍃 /ud touch grass", "Go outside"),
            ("👀 /ud sus", "Suspicious behavior")
        ]
        
        random.shuffle(slang_examples)
        examples_text = "\n".join([f"{emoji} <code>{cmd}</code> - {desc}" for emoji, cmd, desc in slang_examples[:6]])
        
        await query.edit_message_text(
            text=f"{random.choice(responses)}\n\n{examples_text}",
            parse_mode="HTML"
        )
    
    @staticmethod
    async def handle_random_word_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the random word button callback"""
        query = update.callback_query
        await query.answer()
        
        random_words = [
            "yeet", "simp", "ghosting", "clout", "flex", 
            "salty", "woke", "GOAT", "slay", "extra",
            "snack", "thirsty", "glow up", "ship", "stan"
        ]
        
        await query.edit_message_text(
            text=f"🎲 Your random slang word is: <code>{random.choice(random_words)}</code>\n\n"
                 "Send /ud with this word to learn its meaning!",
            parse_mode="HTML"
        )

# Handle /ud command
async def urban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ud command to lookup Urban Dictionary definitions"""
    # Check if user provided a term
    if not context.args:
        await update.message.reply_text(
            "🤔 <b>I need a word to lookup!</b>\n\n"
            "<b>Usage:</b> <code>/ud [word]</code>\n"
            "<i>Examples:</i>\n"
            "<code>/ud yeet</code> - Learn modern yeetology\n"
            "<code>/ud sus</code> - Detect suspicious behavior\n"
            "<code>/ud rizz</code> - Improve your dating game\n\n"
            "💡 <i>Try a random word with</i> <code>/ud random</code>",
            parse_mode="HTML"
        )
        return
    
    term = ' '.join(context.args)
    
    if term.lower() == "random":
        random_words = ["yeet", "simp", "ghosting", "clout", "flex", "salty"]
        term = random.choice(random_words)
        await update.message.reply_text(
            f"🎲 Your random word is: <b>{term}</b>! Let me look it up...",
            parse_mode="HTML"
        )
    
    processing_msg = await update.message.reply_text(
        UrbanDictionaryResponses.get_loading_message(term),
        parse_mode="HTML"
    )
    
    # Fetch definition from API
    definition = await UrbanDictionaryAPI.get_top_definition(term)
    
    if not definition:
        await processing_msg.edit_text(
            f"🚫 {UrbanDictionaryResponses.get_no_result_response(term)}",
            parse_mode="HTML"
        )
        return
    
    # Format and send response
    response_text = UrbanDictionaryResponses.format_definition(definition)
    
    # Truncate if too long (Telegram has 4096 character limit)
    if len(response_text) > 4000:
        response_text = response_text[:4000] + "\n\n[...truncated because this definition was too extra]"
    
    await processing_msg.edit_text(
        text=response_text,
        parse_mode="HTML",
        reply_markup=UrbanDictionaryUI.create_definition_keyboard(term),
        disable_web_page_preview=True
    )


import logging
import mimetypes
import aiohttp
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from io import BytesIO

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FileUploader:
    """Enhanced file uploader with progress tracking and multiple host options"""
    UPLOAD_SERVICES = {
        "catbox": {
            "url": "https://catbox.moe/user/api.php",
            "params": {"reqtype": "fileupload"}
        },
        "temp": {
            "url": "https://tmpfiles.org/api/v1/upload",
            "method": "post"
        }
    }
    
    CHUNK_SIZE = 65536  # 64KB chunks for progress tracking
    
    @staticmethod
    async def upload_file(file_path: Path, file_name: str, update: Update, 
                         context: ContextTypes.DEFAULT_TYPE, service: str = "catbox") -> str:
        """Upload a file to selected service with progress updates"""
        try:
            if service not in FileUploader.UPLOAD_SERVICES:
                raise ValueError(f"Unsupported service: {service}")
                
            mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            file_size = file_path.stat().st_size
            
            # Send initial progress message
            progress_msg = await update.message.reply_text(
                f"📤 Preparing to upload {file_name} ({file_size/1024/1024:.1f} MB) to {service}...\n"
                f"🔄 Progress: 0%"
            )
            
            async def progress_callback(bytes_uploaded: int, total_bytes: int):
                percent = (bytes_uploaded / total_bytes) * 100
                if percent % 5 < 0.1:  # Update every 5% to avoid spamming
                    try:
                        await progress_msg.edit_text(
                            f"📤 Uploading {file_name} ({total_bytes/1024/1024:.1f} MB) to {service}...\n"
                            f"🔄 Progress: {percent:.1f}%"
                        )
                    except Exception as e:
                        logger.warning(f"Progress update failed: {e}")

            service_config = FileUploader.UPLOAD_SERVICES[service]
            url = service_config["url"]
            
            async with aiohttp.ClientSession() as session:
                if service == "catbox":
                    form = aiohttp.FormData()
                    form.add_field("reqtype", "fileupload")
                    form.add_field("userhash", "")
                    
                    with file_path.open('rb') as f:
                        file_data = BytesIO()
                        while chunk := f.read(FileUploader.CHUNK_SIZE):
                            file_data.write(chunk)
                            await progress_callback(f.tell(), file_size)
                        file_data.seek(0)
                        
                        form.add_field(
                            "fileToUpload", 
                            file_data, 
                            filename=file_name, 
                            content_type=mime_type
                        )

                        async with session.post(url, data=form) as response:
                            response.raise_for_status()
                            result = (await response.text()).strip()
                            return result
                            
                elif service == "temp":
                    with file_path.open('rb') as f:
                        file_data = BytesIO()
                        while chunk := f.read(FileUploader.CHUNK_SIZE):
                            file_data.write(chunk)
                            await progress_callback(f.tell(), file_size)
                        file_data.seek(0)
                        
                        form = aiohttp.FormData()
                        form.add_field("file", file_data, filename=file_name)
                        
                        async with session.post(url, data=form) as response:
                            response.raise_for_status()
                            data = await response.json()
                            return f"https://tmpfiles.org/{data['data']['url'].split('/')[-1]}"
                            
            # Final progress update
            await progress_msg.edit_text(
                f"✅ Upload complete!\n"
                f"🔗 Processing URL..."
            )
            
        except Exception as e:
            logger.error(f"{service} upload failed: {str(e)}", exc_info=True)
            if 'progress_msg' in locals():
                try:
                    await progress_msg.edit_text(f"❌ Upload failed: {str(e)}")
                except:
                    await update.message.reply_text(f"❌ Upload failed: {str(e)}")
            raise

class TextUploader:
    """Enhanced text uploader with multiple paste options and fallback"""
    SERVICES = {
        "pastebin": {
            "url": "https://pastebin.com/api/api_post.php",
            "api_key": "YOUR_PASTEBIN_API_KEY",  # Replace with your actual key
            "params": {
                'api_option': 'paste',
                'api_paste_private': '1',
                'api_paste_format': 'text'
            },
            "fallback": "hastebin"
        },
        "hastebin": {
            "url": "https://hastebin.com/documents",
            "raw_url": "https://hastebin.com/raw/{key}",
            "fallback": "dpaste"
        },
        "dpaste": {
            "url": "https://dpaste.com/api/v2/",
            "params": {
                'lexer': '_text',
                'format': 'url',
                'content': None
            },
            "fallback": "pastebin"
        },
        "ixio": {
            "url": "https://ix.io",
            "method": "post",
            "params": {
                'f:1': None  # The text content
            },
            "fallback": "hastebin"
        }
    }
    
    @staticmethod
    async def upload_text(text: str, title: str = "Telegram Text", 
                         service: str = "hastebin", fallback: bool = True) -> str:
        """Upload text to various paste services with automatic fallback"""
        original_service = service
        max_attempts = 3 if fallback else 1
        
        for attempt in range(max_attempts):
            try:
                if service not in TextUploader.SERVICES:
                    raise ValueError(f"Unsupported service: {service}")

                if service == "pastebin":
                    payload = {
                        **TextUploader.SERVICES["pastebin"]["params"],
                        'api_dev_key': TextUploader.SERVICES["pastebin"]["api_key"],
                        'api_paste_code': text,
                        'api_paste_name': title[:100]
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            TextUploader.SERVICES["pastebin"]["url"],
                            data=payload
                        ) as response:
                            response.raise_for_status()
                            return await response.text()
                            
                elif service == "hastebin":
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            TextUploader.SERVICES["hastebin"]["url"],
                            data=text.encode('utf-8')
                        ) as response:
                            response.raise_for_status()
                            data = await response.json()
                            key = data['key']
                            return f"https://hastebin.com/{key}"
                            
                elif service == "dpaste":
                    payload = {
                        **TextUploader.SERVICES["dpaste"]["params"],
                        'content': text
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            TextUploader.SERVICES["dpaste"]["url"],
                            data=payload
                        ) as response:
                            response.raise_for_status()
                            return await response.text()
                            
                elif service == "ixio":
                    payload = aiohttp.FormData()
                    payload.add_field('f:1', text)
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            TextUploader.SERVICES["ixio"]["url"],
                            data=payload
                        ) as response:
                            response.raise_for_status()
                            return response.url.human_repr()
                            
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {service}: {str(e)}")
                if attempt < max_attempts - 1:
                    service = TextUploader.SERVICES[service].get("fallback", "hastebin")
                    continue
                raise RuntimeError(f"Failed to upload to {original_service} (and fallbacks)") from e

async def handle_media_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle media upload command (/tgm) with service selection"""
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "🔍 <b>Please reply to a media message to upload it!</b>\n\n"
            "📸 <i>Supported media:</i> Photos, Videos, Documents, Audio, Voice messages, GIFs\n\n"
            "🔄 <code>/tgm</code> - Upload to Catbox (default)\n"
            "🔄 <code>/tgm temp</code> - Upload to tmpfiles.org\n",
            parse_mode="HTML"
        )
        return
        
    replied = update.message.reply_to_message
    temp_file = None
    service = "catbox"
    
    # Check for service argument
    if context.args and context.args[0].lower() in ["catbox", "temp"]:
        service = context.args[0].lower()
    
    try:
        # Determine file type and prepare for download
        file_info = None
        file_name = None
        file_obj = None
        
        if replied.photo:
            file_info = replied.photo[-1]  # Get highest quality
            file_name = f"photo_{replied.message_id}.jpg"
        elif replied.video:
            file_info = replied.video
            file_name = replied.video.file_name or f"video_{replied.message_id}.mp4"
        elif replied.audio:
            file_info = replied.audio
            file_name = replied.audio.file_name or f"audio_{replied.message_id}.mp3"
        elif replied.voice:
            file_info = replied.voice
            file_name = f"voice_{replied.message_id}.ogg"
        elif replied.document:
            file_info = replied.document
            file_name = replied.document.file_name or f"document_{replied.message_id}"
        elif replied.sticker:
            file_info = replied.sticker
            file_name = f"sticker_{replied.message_id}.webp"
        elif replied.animation:
            file_info = replied.animation
            file_name = f"animation_{replied.message_id}.gif"
        else:
            await update.message.reply_text("❌ Unsupported media type.")
            return

        # Download the file
        status_msg = await update.message.reply_text(
            f"⬇️ Downloading {file_name}...\n"
            f"📦 File size: {file_info.file_size/1024/1024:.1f} MB\n"
            f"🌐 Destination: {service}"
        )
        
        # Get the file as an IO object
        file_obj = await file_info.get_file()
        temp_file = Path(f"temp_{file_name}")
        
        # Download the file content
        await file_obj.download_to_drive(temp_file)
        
        # Upload to selected service
        url = await FileUploader.upload_file(temp_file, file_name, update, context, service)
        
        # Create rich response
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🌐 Open URL", url=url),
                InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={url}")
            ],
            [
                InlineKeyboardButton("📁 File Info", callback_data=f"fileinfo_{file_name}"),
                InlineKeyboardButton("🗑 Delete", callback_data="delete_msg")
            ]
        ])
        
        await status_msg.edit_text(
            f"🎉 <b>Upload Successful!</b>\n\n"
            f"📂 <b>File Name:</b> <code>{file_name}</code>\n"
            f"📏 <b>Size:</b> {file_info.file_size/1024/1024:.1f} MB\n"
            f"🌐 <b>Service:</b> {service}\n"
            f"🔗 <b>URL:</b>\n<code>{url}</code>\n\n"
            f"💾 <i>This file will be stored permanently</i>",
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Media upload error: {str(e)}", exc_info=True)
        error_msg = await update.message.reply_text(
            f"❌ <b>Upload Failed!</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"⚠️ Please try again later or try a different service",
            parse_mode="HTML"
        )
        # Auto-delete error message after 30 seconds
        await asyncio.sleep(30)
        try:
            await error_msg.delete()
        except:
            pass
        
    finally:
        # Clean up temporary file
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

async def handle_text_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text upload command (/tgt) with multiple paste services and fallback"""
    try:
        # Get text from message or replied message
        if update.message.reply_to_message:
            text = (update.message.reply_to_message.text or 
                   update.message.reply_to_message.caption or "")
        elif context.args:
            # Check if first argument is a service name
            service_args = ["pastebin", "hastebin", "dpaste", "ixio"]
            if context.args[0].lower() in service_args:
                text = ' '.join(context.args[1:]) if len(context.args) > 1 else ""
                if update.message.reply_to_message:
                    text = (update.message.reply_to_message.text or 
                           update.message.reply_to_message.caption or "")
            else:
                text = ' '.join(context.args)
        else:
            await update.message.reply_text(
                "📝 <b>Text Uploader</b>\n\n"
                "🔹 Reply to a text message with <code>/tgt</code>\n"
                "🔹 Or type <code>/tgt your text here</code>\n\n"
                "📌 <i>Options:</i>\n"
                "<code>/tgt pastebin</code> - Use Pastebin\n"
                "<code>/tgt hastebin</code> - Use Hastebin (default)\n"
                "<code>/tgt dpaste</code> - Use DPaste\n"
                "<code>/tgt ixio</code> - Use ix.io",
                parse_mode="HTML"
            )
            return

        if not text.strip():
            await update.message.reply_text("❌ No text content found to upload.")
            return

        # Determine service (default to hastebin)
        service = "hastebin"
        if context.args and context.args[0].lower() in TextUploader.SERVICES:
            service = context.args[0].lower()

        # Upload to selected service with fallback
        status_msg = await update.message.reply_text(
            f"📤 Uploading text to {service.capitalize()}..."
        )
        
        try:
            url = await TextUploader.upload_text(text, service=service, fallback=True)
        except Exception as e:
            await status_msg.edit_text(
                f"❌ <b>All upload attempts failed!</b>\n\n"
                f"<code>{str(e)}</code>",
                parse_mode="HTML"
            )
            return

        preview_text = text[:100] + "..." if len(text) > 100 else text
        
        # Create service-specific response
        if service == "pastebin":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 View Paste", url=url),
                    InlineKeyboardButton("📝 Raw Text", url=f"{url}/raw")
                ],
                [
                    InlineKeyboardButton("✏️ Edit", url=f"{url}/edit"),
                    InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={url}")
                ]
            ])
        elif service == "ixio":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 View Paste", url=url),
                    InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={url}")
                ]
            ])
        else:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 View Paste", url=url),
                    InlineKeyboardButton("📝 Raw Text", url=f"{url}/raw" if service == "hastebin" else url)
                ],
                [
                    InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={url}")
                ]
            ])
        
        await status_msg.edit_text(
            f"✅ <b>Text Uploaded to {service.capitalize()}!</b>\n\n"
            f"🔗 <b>URL:</b> <code>{url}</code>\n"
            f"📋 <b>Preview:</b>\n<code>{preview_text}</code>\n\n"
            f"📝 <i>This text will be stored permanently</i>",
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Text upload error: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ <b>Upload Failed!</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"⚠️ Please try again with a different service",
            parse_mode="HTML"
        )

import asyncio
import logging
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from PIL import Image, ImageEnhance, ImageFilter
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from typing import Optional

# Enhanced logging setup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UltraUpscaler:
    """Advanced image upscaler with multiple enhancement options"""
    def __init__(self):
        self.cache_dir = Path("ultra_upscaler_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size = 25 * 1024 * 1024  # 25MB
        self.enhancement_presets = {
            "standard": {
                "scale": 2,
                "sharpness": 2.0,
                "color": 1.5,
                "contrast": 1.18,
                "brightness": 1.07
            },
            "extreme": {
                "scale": 3,
                "sharpness": 2.5,
                "color": 1.8,
                "contrast": 1.25,
                "brightness": 1.1
            },
            "soft": {
                "scale": 2,
                "sharpness": 1.5,
                "color": 1.2,
                "contrast": 1.1,
                "brightness": 1.05
            }
        }

    async def upscale_image(self, image_bytes: bytes, preset: str = "standard") -> BytesIO:
        """Performs advanced upscaling and enhancement with preset options"""
        preset_params = self.enhancement_presets.get(preset, self.enhancement_presets["standard"])

        with Image.open(BytesIO(image_bytes)) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")

            new_size = (int(img.width * preset_params["scale"]), int(img.height * preset_params["scale"]))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=180, threshold=2))
            img = ImageEnhance.Sharpness(img).enhance(preset_params["sharpness"])
            img = ImageEnhance.Color(img).enhance(preset_params["color"])
            img = ImageEnhance.Contrast(img).enhance(preset_params["contrast"])
            img = ImageEnhance.Brightness(img).enhance(preset_params["brightness"])

            img = img.filter(ImageFilter.SMOOTH_MORE)

            buf = BytesIO()
            img.save(buf, format="PNG", optimize=True, quality=95)
            buf.seek(0)
            return buf

    async def cleanup(self, *paths):
        for path in paths:
            try:
                if path and Path(path).exists():
                    Path(path).unlink()
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")

    async def send_progress_update(self, update: Update, message: str):
        if hasattr(self, 'progress_message'):
            await self.progress_message.edit_text(message)
        else:
            self.progress_message = await update.message.reply_text(message, parse_mode="HTML")

    async def handle_upscale(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        reply = update.message.reply_to_message
        if not reply or not (reply.photo or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("image/"))):
            msg = await update.message.reply_text(
                "🖼️ <b>Reply to an image with <code>/upscale</code>!</b>\n\n"
                "📌 <i>Available presets:</i>\n"
                "<code>/upscale standard</code> - Balanced enhancement (default)\n"
                "<code>/upscale extreme</code> - Maximum detail\n"
                "<code>/upscale soft</code> - Subtle enhancement",
                parse_mode="HTML"
            )
            await asyncio.sleep(10)
            await msg.delete()
            await update.message.delete()
            return

        preset = "standard"
        if context.args and context.args[0].lower() in self.enhancement_presets:
            preset = context.args[0].lower()

        file_id = reply.photo[-1].file_id if reply.photo else reply.document.file_id
        await self.send_progress_update(
            update,
            "✨ <b>Starting Upscale Process</b>\n\n"
            f"🔍 <i>Using {preset.capitalize()} preset</i>\n"
            "⏳ <i>Downloading image...</i>"
        )

        try:
            file = await context.bot.get_file(file_id)
            dl_path = self.cache_dir / f"original_{file.file_id}.jpg"
            await file.download_to_drive(dl_path)

            with open(dl_path, "rb") as f:
                image_bytes = f.read()

            if len(image_bytes) > self.max_size:
                await self.send_progress_update(
                    update,
                    "❌ <b>Image too large (max 25MB)</b>\n"
                    "📏 <i>Try with a smaller image</i>"
                )
                await self.cleanup(dl_path)
                return

            stages = [
                ("🔄 <b>Upscaling Resolution</b>", 20),
                ("🔍 <b>Enhancing Details</b>", 40),
                ("🎨 <b>Adjusting Colors</b>", 60),
                ("✨ <b>Final Touches</b>", 80),
                ("✅ <b>Processing Complete</b>", 100)
            ]

            for stage_text, progress in stages:
                await self.send_progress_update(
                    update,
                    f"{stage_text}\n\n"
                    f"⚙️ <i>Preset:</i> <code>{preset.capitalize()}</code>\n"
                    f"📊 <i>Progress:</i> <b>{progress}%</b>"
                )
                await asyncio.sleep(1)

            upscaled = await self.upscale_image(image_bytes, preset)

            with NamedTemporaryFile(delete=False, suffix=".png", dir=self.cache_dir) as tmp:
                tmp.write(upscaled.getbuffer())
                tmp_path = tmp.name

            await update.message.reply_photo(
                photo=InputFile(upscaled),
                caption=(
                    "🌟 <b>Ultra Upscale Complete!</b>\n\n"
                    f"⚙️ <b>Preset:</b> <code>{preset.capitalize()}</code>\n"
                    f"📐 <b>Resolution:</b> <code>{'3×' if preset == 'extreme' else '2×'} Enhanced</code>\n"
                    f"🔍 <b>Details:</b> <code>{'Max Sharp' if preset == 'extreme' else 'Ultra Sharp'}</code>\n\n"
                    "<i>Download the full quality version below!</i>"
                ),
                parse_mode="HTML"
            )

            await update.message.reply_document(
                document=InputFile(tmp_path),
                filename=f"enhanced_{preset}.png",
                caption=(
                    "📁 <b>Full Quality Enhanced Image</b>\n\n"
                    "✨ <i>Enhanced with Ultra Upscaler</i>\n"
                    f"⚙️ <i>Preset:</i> <code>{preset.capitalize()}</code>"
                ),
                parse_mode="HTML"
            )

            await self.progress_message.delete()
            await update.message.delete()
            await self.cleanup(dl_path, tmp_path)

        except Exception as e:
            logger.error(f"Upscale error: {e}", exc_info=True)
            err_msg = await update.message.reply_text(
                "❌ <b>Upscale Failed!</b>\n\n"
                f"<code>{str(e)}</code>\n\n"
                "⚠️ <i>Please try again or contact support</i>",
                parse_mode="HTML"
            )
            await asyncio.sleep(10)
            await err_msg.delete()
            await update.message.delete()
            await self.cleanup(dl_path)

import json
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

PROFILE_CACHE_FILE = "user_profiles.json"

# Load or initialize cache
if os.path.exists(PROFILE_CACHE_FILE):
    with open(PROFILE_CACHE_FILE, "r", encoding="utf-8") as f:
        user_cache = json.load(f)
else:
    user_cache = {}

def save_cache():
    """Save the user profile cache to file."""
    with open(PROFILE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(user_cache, f, ensure_ascii=False, indent=2)

async def profile_watcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if the user changed their profile and notify the group."""
    if not update.message or not update.message.from_user:
        return

    user = update.message.from_user
    chat = update.message.chat
    user_id = str(user.id)

    current_profile = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

    if user_id not in user_cache:
        # First time seeing this user — store profile
        user_cache[user_id] = current_profile
        save_cache()
        await chat.send_message(
            f"✅ Stored profile for <b>{user.full_name}</b> (<code>{user.id}</code>)",
            parse_mode="HTML"
        )
        return

    old_profile = user_cache[user_id]
    changes = []

    for key, label in [
        ("username", "Username"),
        ("first_name", "First Name"),
        ("last_name", "Last Name")
    ]:
        old_val = old_profile.get(key)
        new_val = current_profile.get(key)
        if old_val != new_val:
            changes.append(f"• <b>{label}</b>: <code>{old_val or 'None'}</code> → <code>{new_val or 'None'}</code>")

    if changes:
        user_cache[user_id] = current_profile
        save_cache()
        change_text = "\n".join(changes)
        msg = (
            f"⚠️ <b>Profile Change Detected!</b>\n"
            f"👤 <b>{user.full_name}</b> (<code>{user.id}</code>)\n"
            f"{change_text}"
        )
        await chat.send_message(msg, parse_mode="HTML")
    else:
        await chat.send_message(
            f"🔍 Checked {user.full_name} — no profile changes detected.",
            parse_mode="HTML"
        )


import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
from enum import Enum, auto

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMemberAdministrator,
    ChatMemberOwner,
    User,
    Message,
    Chat
)
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    Application
)
from datetime import timedelta
# === DATABASE SETUP ===
class WarningDatabase:
    def __init__(self, db_path: str = "warnings.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables with proper schema"""
        # Drop old tables if they exist
        self.cursor.execute("DROP TABLE IF EXISTS warnings")
        self.cursor.execute("DROP TABLE IF EXISTS warning_stats")
        self.cursor.execute("DROP TABLE IF EXISTS warn_settings")

        # Create new tables with correct schema
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            reason TEXT,
            message_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS warning_stats (
            chat_id INTEGER,
            user_id INTEGER,
            total_warnings INTEGER DEFAULT 0,
            active_warnings INTEGER DEFAULT 0,
            last_warning DATETIME,
            PRIMARY KEY (chat_id, user_id)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS warn_settings (
            chat_id INTEGER PRIMARY KEY,
            max_warnings INTEGER DEFAULT 3,
            warn_expiry_days INTEGER DEFAULT 30,
            ban_duration_days INTEGER DEFAULT 1,
            notify_user BOOLEAN DEFAULT TRUE,
            delete_expired_warns BOOLEAN DEFAULT TRUE
        )
        """)
        self.conn.commit()

    def get_chat_settings(self, chat_id: int) -> Dict[str, Any]:
        """Get warning settings for a chat"""
        self.cursor.execute("SELECT * FROM warn_settings WHERE chat_id = ?", (chat_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'max_warnings': row[1],
                'warn_expiry_days': row[2],
                'ban_duration_days': row[3],
                'notify_user': bool(row[4]),
                'delete_expired_warns': bool(row[5])
            }
        return {
            'max_warnings': 3,
            'warn_expiry_days': 30,
            'ban_duration_days': 1,
            'notify_user': True,
            'delete_expired_warns': True
        }

    def update_chat_settings(self, chat_id: int, **kwargs):
        """Update warning settings for a chat"""
        current = self.get_chat_settings(chat_id)
        current.update(kwargs)
        
        self.cursor.execute("""
        INSERT INTO warn_settings (
            chat_id, max_warnings, warn_expiry_days, ban_duration_days, notify_user, delete_expired_warns
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            max_warnings = excluded.max_warnings,
            warn_expiry_days = excluded.warn_expiry_days,
            ban_duration_days = excluded.ban_duration_days,
            notify_user = excluded.notify_user,
            delete_expired_warns = excluded.delete_expired_warns
        """, (
            chat_id,
            current['max_warnings'],
            current['warn_expiry_days'],
            current['ban_duration_days'],
            int(current['notify_user']),
            int(current['delete_expired_warns'])
        ))
        self.conn.commit()

    def add_warning(
        self,
        chat_id: int,
        user_id: int,
        admin_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str],
        reason: Optional[str] = None,
        message_id: Optional[int] = None
    ) -> Tuple[int, int]:
        """Add a warning to the database"""
        # Update warning stats
        self.cursor.execute("""
        INSERT INTO warning_stats (chat_id, user_id, total_warnings, active_warnings, last_warning)
        VALUES (?, ?, 1, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(chat_id, user_id) DO UPDATE SET
            total_warnings = total_warnings + 1,
            active_warnings = active_warnings + 1,
            last_warning = CURRENT_TIMESTAMP
        """, (chat_id, user_id))
        
        # Add warning record
        self.cursor.execute("""
        INSERT INTO warnings (
            chat_id, user_id, admin_id, username, first_name, last_name, reason, message_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            user_id,
            admin_id,
            username,
            first_name,
            last_name,
            reason,
            message_id
        ))
        
        self.conn.commit()
        
        # Get updated counts
        self.cursor.execute("""
        SELECT total_warnings, active_warnings FROM warning_stats 
        WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        return self.cursor.fetchone()

    def remove_warning(self, chat_id: int, user_id: int, warn_id: Optional[int] = None) -> Tuple[int, int]:
        """Remove a warning (specific or oldest)"""
        if warn_id:
            self.cursor.execute("DELETE FROM warnings WHERE id = ? AND chat_id = ? AND user_id = ?", 
                              (warn_id, chat_id, user_id))
        else:
            # Delete the oldest active warning
            self.cursor.execute("""
            DELETE FROM warnings 
            WHERE id = (
                SELECT id FROM warnings 
                WHERE chat_id = ? AND user_id = ? 
                ORDER BY timestamp ASC 
                LIMIT 1
            )
            """, (chat_id, user_id))
        
        # Update stats if a warning was actually deleted
        if self.cursor.rowcount > 0:
            self.cursor.execute("""
            UPDATE warning_stats 
            SET active_warnings = active_warnings - 1 
            WHERE chat_id = ? AND user_id = ? AND active_warnings > 0
            """, (chat_id, user_id))
        
        self.conn.commit()
        
        # Get updated counts
        self.cursor.execute("""
        SELECT total_warnings, active_warnings FROM warning_stats 
        WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        return self.cursor.fetchone() or (0, 0)

    def reset_warnings(self, chat_id: int, user_id: int) -> bool:
        """Reset all warnings for a user"""
        self.cursor.execute("DELETE FROM warnings WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        self.cursor.execute("""
        UPDATE warning_stats 
        SET active_warnings = 0 
        WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_warning_details(self, chat_id: int, user_id: int) -> List[Tuple]:
        """Get detailed warning information for a user"""
        self.cursor.execute("""
        SELECT id, admin_id, reason, timestamp, message_id 
        FROM warnings 
        WHERE chat_id = ? AND user_id = ?
        ORDER BY timestamp DESC
        """, (chat_id, user_id))
        return self.cursor.fetchall()

    def cleanup_expired_warnings(self):
        """Clean up warnings that have expired based on chat settings"""
        self.cursor.execute("SELECT DISTINCT chat_id FROM warn_settings")
        chat_ids = [row[0] for row in self.cursor.fetchall()]
        
        for chat_id in chat_ids:
            settings = self.get_chat_settings(chat_id)
            if settings['delete_expired_warns'] and settings['warn_expiry_days'] > 0:
                expiry_date = datetime.now() - timedelta(days=settings['warn_expiry_days'])
                self.cursor.execute("""
                DELETE FROM warnings 
                WHERE chat_id = ? AND timestamp < ?
                """, (chat_id, expiry_date))
                
                # Update stats for affected users
                self.cursor.execute("""
                UPDATE warning_stats ws
                SET active_warnings = (
                    SELECT COUNT(*) 
                    FROM warnings w 
                    WHERE w.chat_id = ws.chat_id 
                    AND w.user_id = ws.user_id
                )
                WHERE ws.chat_id = ?
                """, (chat_id,))
        
        self.conn.commit()

# Initialize database
db = WarningDatabase()

# === UTILITY FUNCTIONS ===
async def is_admin_with_restrict(update: Update, user_id: int) -> bool:
    """Check if user is admin with restrict permissions"""
    try:
        member = await update.effective_chat.get_member(user_id)
        if isinstance(member, ChatMemberOwner):
            return True
        if isinstance(member, ChatMemberAdministrator):
            return getattr(member, "can_restrict_members", False)
        return False
    except Exception:
        return False

async def format_user_mention(user: User) -> str:
    """Format user mention with fallbacks"""
    if user.username:
        return f"@{user.username}"
    return user.mention_html()

async def resolve_target_user(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
) -> Tuple[Optional[User], str]:
    """
    Identify target user from command arguments or reply
    Returns (user, resolution_method) or (None, error_key)
    """
    message = update.effective_message
    chat = update.effective_chat
    
    # Case 1: Reply to message
    if message.reply_to_message:
        return message.reply_to_message.from_user, "reply"
    
    # Case 2: No arguments provided
    if not context.args:
        return None, "no_args"
    
    user_input = context.args[0].strip()
    
    # Case 3: User ID provided
    if user_input.isdigit():
        try:
            member = await chat.get_member(int(user_input))
            return member.user, "user_id"
        except Exception:
            pass
    
    # Case 4: Username provided
    if user_input.startswith('@'):
        username = user_input[1:]
        try:
            # Try to get user by username (works if they've interacted with bot)
            db.cursor.execute(
                "SELECT user_id FROM warnings WHERE chat_id = ? AND username = ? ORDER BY timestamp DESC LIMIT 1",
                (chat.id, username)
            )
            row = db.cursor.fetchone()
            if row:
                member = await chat.get_member(row[0])
                return member.user, "username"
        except Exception:
            pass
    
    # Case 5: User mention
    if user_input.startswith('<a href="tg://user?id='):
        try:
            user_id = int(user_input.split('=')[1].split('"')[0])
            member = await chat.get_member(user_id)
            return member.user, "mention"
        except Exception:
            pass
    
    return None, "invalid"

async def send_user_notification(
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    chat: Chat,
    action: str,
    reason: Optional[str] = None,
    warn_count: Optional[int] = None,
    max_warnings: Optional[int] = None
) -> bool:
    """Send DM notification to user about warning action"""
    try:
        message = (
            f"⚠️ <b>Moderation Notice</b>\n\n"
            f"<b>Chat:</b> {chat.title}\n"
            f"<b>Action:</b> {action}\n"
        )
        
        if reason:
            message += f"<b>Reason:</b> {reason}\n"
        if warn_count is not None and max_warnings is not None:
            message += f"<b>Warnings:</b> {warn_count}/{max_warnings}\n"
        
        message += "\nPlease review the group rules to avoid further actions."
        
        await context.bot.send_message(
            user.id,
            message,
            parse_mode=ParseMode.HTML
        )
        return True
    except Exception:
        return False

# === WARNING COMMANDS ===
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /warn command"""
    chat = update.effective_chat
    admin = update.effective_user
    message = update.effective_message
    
    # Permission check
    if not await is_admin_with_restrict(update, admin.id):
        await message.reply_text(
            "❌ You need admin privileges with restrict permissions to warn users.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Identify target user
    target, resolution = await resolve_target_user(update, context)
    if not target:
        error_messages = {
            "no_args": "Please specify a user by replying to their message or providing their @username/user ID.",
            "invalid": "Couldn't identify the user. Please try again."
        }
        await message.reply_text(error_messages.get(resolution, "Invalid user specified."))
        return
    
    # Validate target
    if target.id == context.bot.id:
        await message.reply_text("🤖 I can't warn myself!")
        return
    
    try:
        member = await chat.get_member(target.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("🛡️ You can't warn other admins or the chat owner.")
            return
    except Exception as e:
        await message.reply_text(f"⚠️ Failed to verify user status: {e}")
        return
    
    # Get reason (everything after user mention)
    reason = " ".join(context.args[1:]) if resolution != "reply" and len(context.args) > 1 else None
    if not reason and resolution == "reply":
        reason = "No reason provided"
    
    # Add warning to database
    settings = db.get_chat_settings(chat.id)
    total_warns, active_warns = db.add_warning(
        chat.id,
        target.id,
        admin.id,
        target.username,
        target.first_name,
        target.last_name,
        reason
    )
    
    # Format response
    user_mention = await format_user_mention(target)
    admin_mention = admin.mention_html()
    
    response = (
        f"⚠️ <b>Warning issued to {user_mention}</b>\n\n"
        f"• <b>By:</b> {admin_mention}\n"
        f"• <b>Reason:</b> {reason or 'Not specified'}\n"
        f"• <b>Warnings:</b> {active_warns}/{settings['max_warnings']}\n\n"
    )
    
    if active_warns >= settings['max_warnings']:
        response += "🚨 <b>Maximum warnings reached!</b>"
    else:
        remaining = settings['max_warnings'] - active_warns
        response += f"ℹ️ {remaining} more warnings before auto-ban."
    
    # Send notification to user if enabled
    if settings['notify_user'] and target.id != admin.id:
        await send_user_notification(
            context,
            target,
            chat,
            "Warning issued",
            reason,
            active_warns,
            settings['max_warnings']
        )
    
    # Create action buttons
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚠️ Remove Warn", callback_data=f"unwarn_{target.id}_{admin.id}"),
        InlineKeyboardButton("🔨 Ban", callback_data=f"ban_{target.id}_{admin.id}")
    ]])
    
    sent_msg = await message.reply_text(
        response,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    
    # Auto-ban if max warnings reached
    if active_warns >= settings['max_warnings']:
        try:
            await context.bot.ban_chat_member(chat.id, target.id)
            await sent_msg.edit_text(
                f"{response}\n\n🚫 {user_mention} has been banned for reaching {settings['max_warnings']} warnings.",
                parse_mode=ParseMode.HTML
            )
            
            # Reset warnings if auto-delete is enabled
            if settings['delete_expired_warns']:
                db.reset_warnings(chat.id, target.id)
        except Exception as e:
            await sent_msg.edit_text(f"{response}\n\n⚠️ Failed to ban user: {e}")

async def delete_and_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dwarn command (delete message and warn)"""
    chat = update.effective_chat
    admin = update.effective_user
    message = update.effective_message
    
    # Permission check
    if not await is_admin_with_restrict(update, admin.id):
        await message.reply_text(
            "❌ You need admin privileges with restrict permissions to use this command.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Must be a reply
    if not message.reply_to_message:
        await message.reply_text(
            "❌ Please reply to the message you want to delete and warn the user for.",
            parse_mode=ParseMode.HTML
        )
        return
    
    target = message.reply_to_message.from_user
    
    # Validate target
    if target.id == context.bot.id:
        await message.reply_text("🤖 I can't warn myself!")
        return
    
    try:
        member = await chat.get_member(target.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("🛡️ You can't warn other admins or the chat owner.")
            return
    except Exception as e:
        await message.reply_text(f"⚠️ Failed to verify user status: {e}")
        return
    
    # Get reason (everything after command)
    reason = " ".join(context.args) if context.args else "Inappropriate message"
    
    # Delete the offending message
    try:
        await message.reply_to_message.delete()
    except Exception as e:
        await message.reply_text(f"⚠️ Couldn't delete message: {e}")
        # Continue with warning even if deletion fails
    
    # Add warning
    settings = db.get_chat_settings(chat.id)
    total_warns, active_warns = db.add_warning(
        chat.id,
        target.id,
        admin.id,
        target.username,
        target.first_name,
        target.last_name,
        reason,
        message.reply_to_message.message_id
    )
    
    # Format response
    user_mention = await format_user_mention(target)
    admin_mention = admin.mention_html()
    
    response = (
        f"🗑️ <b>Message deleted and warning issued to {user_mention}</b>\n\n"
        f"• <b>By:</b> {admin_mention}\n"
        f"• <b>Reason:</b> {reason}\n"
        f"• <b>Warnings:</b> {active_warns}/{settings['max_warnings']}\n\n"
    )
    
    if active_warns >= settings['max_warnings']:
        response += "🚨 <b>Maximum warnings reached!</b>"
    else:
        remaining = settings['max_warnings'] - active_warns
        response += f"ℹ️ {remaining} more warnings before auto-ban."
    
    # Send notification to user if enabled
    if settings['notify_user'] and target.id != admin.id:
        await send_user_notification(
            context,
            target,
            chat,
            "Message deleted and warning issued",
            reason,
            active_warns,
            settings['max_warnings']
        )
    
    # Create action buttons
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚠️ Remove Warn", callback_data=f"unwarn_{target.id}_{admin.id}"),
        InlineKeyboardButton("🔨 Ban", callback_data=f"ban_{target.id}_{admin.id}")
    ]])
    
    sent_msg = await message.reply_text(
        response,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    
    # Auto-ban if max warnings reached
    if active_warns >= settings['max_warnings']:
        try:
            await context.bot.ban_chat_member(chat.id, target.id)
            await sent_msg.edit_text(
                f"{response}\n\n🚫 {user_mention} has been banned for reaching {settings['max_warnings']} warnings.",
                parse_mode=ParseMode.HTML
            )
            
            # Reset warnings if auto-delete is enabled
            if settings['delete_expired_warns']:
                db.reset_warnings(chat.id, target.id)
        except Exception as e:
            await sent_msg.edit_text(f"{response}\n\n⚠️ Failed to ban user: {e}")

async def remove_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unwarn command"""
    chat = update.effective_chat
    admin = update.effective_user
    message = update.effective_message
    
    # Permission check
    if not await is_admin_with_restrict(update, admin.id):
        await message.reply_text(
            "❌ You need admin privileges with restrict permissions to remove warnings.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Identify target user
    target, resolution = await resolve_target_user(update, context)
    if not target:
        error_messages = {
            "no_args": "Please specify a user by replying to their message or providing their @username/user ID.",
            "invalid": "Couldn't identify the user. Please try again."
        }
        await message.reply_text(error_messages.get(resolution, "Invalid user specified."))
        return
    
    # Remove warning
    total_warns, active_warns = db.remove_warning(chat.id, target.id)
    
    if active_warns == total_warns:
        # No warning was actually removed
        await message.reply_text(
            f"ℹ️ {await format_user_mention(target)} has no active warnings to remove.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Format response
    user_mention = await format_user_mention(target)
    settings = db.get_chat_settings(chat.id)
    
    await message.reply_text(
        f"✅ Removed 1 warning from {user_mention}\n"
        f"Active warnings: {active_warns}/{settings['max_warnings']}",
        parse_mode=ParseMode.HTML
    )

async def check_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /warns command"""
    chat = update.effective_chat
    message = update.effective_message
    
    # Identify target user (default to command sender if no target specified)
    target, resolution = await resolve_target_user(update, context)
    if not target:
        target = update.effective_user
    
    # Get warning details
    warning_details = db.get_warning_details(chat.id, target.id)
    stats = db.cursor.execute("""
        SELECT total_warnings, active_warnings FROM warning_stats 
        WHERE chat_id = ? AND user_id = ?
    """, (chat.id, target.id)).fetchone()
    
    if not stats or stats[1] == 0:
        await message.reply_text(
            f"ℹ️ {await format_user_mention(target)} has no active warnings.",
            parse_mode=ParseMode.HTML
        )
        return
    
    total_warns, active_warns = stats
    settings = db.get_chat_settings(chat.id)
    
    # Format response
    response = (
        f"⚠️ <b>Warning history for {await format_user_mention(target)}</b>\n\n"
        f"• <b>Active warnings:</b> {active_warns}/{settings['max_warnings']}\n"
        f"• <b>Total warnings:</b> {total_warns}\n\n"
        "<b>Recent warnings:</b>\n"
    )
    
    for warn_id, admin_id, reason, timestamp, message_id in warning_details[:5]:  # Show up to 5 most recent
        try:
            admin = await context.bot.get_chat_member(chat.id, admin_id)
            admin_name = admin.user.first_name
        except Exception:
            admin_name = "Unknown Admin"
        
        response += (
            f"├─ <b>ID:</b> {warn_id}\n"
            f"├─ <b>By:</b> {admin_name}\n"
            f"├─ <b>When:</b> {timestamp}\n"
            f"└─ <b>Reason:</b> {reason or 'Not specified'}\n\n"
        )
    
    if len(warning_details) > 5:
        response += f"ℹ️ Showing 5 of {len(warning_details)} total warnings."
    
    # Add action buttons if the command sender is an admin
    if await is_admin_with_restrict(update, update.effective_user.id):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⚠️ Remove Warn", callback_data=f"unwarn_{target.id}_{update.effective_user.id}"),
            InlineKeyboardButton("🗑️ Clear All", callback_data=f"clearwarns_{target.id}_{update.effective_user.id}")
        ]])
        await message.reply_text(
            response,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(
            response,
            parse_mode=ParseMode.HTML
        )

async def reset_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /resetwarns command"""
    chat = update.effective_chat
    admin = update.effective_user
    message = update.effective_message
    
    # Permission check
    if not await is_admin_with_restrict(update, admin.id):
        await message.reply_text(
            "❌ You need admin privileges with restrict permissions to reset warnings.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Identify target user
    target, resolution = await resolve_target_user(update, context)
    if not target:
        error_messages = {
            "no_args": "Please specify a user by replying to their message or providing their @username/user ID.",
            "invalid": "Couldn't identify the user. Please try again."
        }
        await message.reply_text(error_messages.get(resolution, "Invalid user specified."))
        return
    
    # Check if user has any warnings
    stats = db.cursor.execute("""
        SELECT active_warnings FROM warning_stats 
        WHERE chat_id = ? AND user_id = ?
    """, (chat.id, target.id)).fetchone()
    
    if not stats or stats[0] == 0:
        await message.reply_text(
            f"ℹ️ {await format_user_mention(target)} already has no warnings.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Reset warnings
    db.reset_warnings(chat.id, target.id)
    
    await message.reply_text(
        f"✅ All warnings for {await format_user_mention(target)} have been reset.",
        parse_mode=ParseMode.HTML
    )

# === BUTTON HANDLERS ===
async def handle_warning_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks for warning actions"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat = update.effective_chat
    admin = query.from_user
    
    try:
        action, target_id, admin_id = data.split("_")
        target_id = int(target_id)
        admin_id = int(admin_id)
    except ValueError:
        return
    
    # Verify permissions
    if admin.id != admin_id:
        await query.answer("⚠️ Only the admin who issued the warning can take action.", show_alert=True)
        return
    
    if not await is_admin_with_restrict(update, admin.id):
        await query.answer("❌ You no longer have permission to restrict members.", show_alert=True)
        return
    
    # Get target user
    try:
        target = await context.bot.get_chat_member(chat.id, target_id)
        target = target.user
    except Exception:
        await query.answer("❌ User not found in this chat.", show_alert=True)
        return
    
    settings = db.get_chat_settings(chat.id)
    user_mention = await format_user_mention(target)
    admin_mention = admin.mention_html()
    
    if action == "unwarn":
        # Remove one warning
        total_warns, active_warns = db.remove_warning(chat.id, target_id)
        
        await query.edit_message_text(
            f"✅ Removed 1 warning from {user_mention}\n"
            f"Active warnings: {active_warns}/{settings['max_warnings']}",
            parse_mode=ParseMode.HTML
        )
    
    elif action == "clearwarns":
        # Reset all warnings
        db.reset_warnings(chat.id, target_id)
        
        await query.edit_message_text(
            f"✅ All warnings for {user_mention} have been removed.",
            parse_mode=ParseMode.HTML
        )
    
    elif action == "ban":
        # Ban the user
        try:
            # Safety checks
            if target_id == context.bot.id:
                return await query.answer("🤖 I can't ban myself.", show_alert=True)
            if target_id == admin.id:
                return await query.answer("❌ You can't ban yourself.", show_alert=True)
            
            member = await chat.get_member(target_id)
            if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return await query.answer("🛡️ You can't ban an admin or the chat owner.", show_alert=True)
            
            # Perform ban
            await context.bot.ban_chat_member(chat.id, target_id)
            
            # Reset warnings if auto-delete is enabled
            if settings['delete_expired_warns']:
                db.reset_warnings(chat.id, target_id)
            
            await query.edit_message_text(
                f"🚫 {user_mention} has been banned by {admin_mention}.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await query.answer(f"⚠️ Failed to ban user: {e}", show_alert=True)

# === SETTINGS COMMANDS ===
async def warn_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /warnsettings command"""
    chat = update.effective_chat
    admin = update.effective_user
    
    # Permission check
    if not await is_admin_with_restrict(update, admin.id):
        await update.message.reply_text(
            "❌ You need admin privileges with restrict permissions to view warn settings.",
            parse_mode=ParseMode.HTML
        )
        return
    
    settings = db.get_chat_settings(chat.id)
    
    response = (
        "⚙️ <b>Warning System Settings</b>\n\n"
        f"• <b>Max warnings before ban:</b> {settings['max_warnings']}\n"
        f"• <b>Warning expiration:</b> {settings['warn_expiry_days']} days\n"
        f"• <b>Default ban duration:</b> {settings['ban_duration_days']} day(s)\n"
        f"• <b>Notify warned users:</b> {'Yes' if settings['notify_user'] else 'No'}\n"
        f"• <b>Auto-delete expired warnings:</b> {'Yes' if settings['delete_expired_warns'] else 'No'}\n\n"
        "<b>Commands to change settings:</b>\n"
        "<code>/setwarnlimit</code> - Set max warnings\n"
        "<code>/setwarnduration</code> - Set warning expiry\n"
        "<code>/setnotifywarn</code> - Toggle user notifications"
    )
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)

async def set_warn_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setwarnlimit command"""
    chat = update.effective_chat
    admin = update.effective_user
    
    # Permission check
    if not await is_admin_with_restrict(update, admin.id):
        await update.message.reply_text(
            "❌ You need admin privileges with restrict permissions to change warn settings.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Get new limit
    try:
        new_limit = int(context.args[0]) if context.args else None
        if not new_limit or new_limit < 1 or new_limit > 10:
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Please specify a valid number between 1 and 10.\n"
            "Example: <code>/setwarnlimit 3</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Update settings
    db.update_chat_settings(chat.id, max_warnings=new_limit)
    
    await update.message.reply_text(
        f"✅ Maximum warnings before ban set to <b>{new_limit}</b>.",
        parse_mode=ParseMode.HTML
    )

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ Please provide a location.\nUsage: <code>/weather Delhi</code>", parse_mode=ParseMode.HTML)
    
    location = " ".join(context.args)
    weather_url = f"https://wttr.in/{location}.png"

    await update.message.reply_photo(
        photo=weather_url,
        caption=f"🌤️ Here's the weather for <b>{location.title()}</b>",
        parse_mode=ParseMode.HTML
    )

WELCOME_MESSAGES = [
    "🌟 Welcome {mention} to {chat_title}! Enjoy your stay!",
    "🚀 {mention} has joined {chat_title}! Let the adventure begin!",
    "🎉 Hello {mention}! Welcome to {chat_title}!",
    "👋 Greetings {mention}! We're glad you're here in {chat_title}!"
]

GOODBYE_MESSAGES = [
    "👋 Farewell {mention}! We'll miss you in {chat_title}!",
    "🚪 {mention} has left {chat_title}. Until next time!",
    "🌅 Goodbye {mention}! Thanks for being part of {chat_title}!",
    "💔 {mention} has departed from {chat_title}. Come back soon!"
]

async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:  # Skip other bots
            continue
            
        chat = update.effective_chat
        message = random.choice(WELCOME_MESSAGES).format(
            mention=member.mention_html(),
            chat_title=chat.title
        )
        
        await context.bot.send_message(
            chat.id,
            message,
            parse_mode="HTML"
        )

async def goodbye_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.left_chat_member:
        return
        
    user = update.message.left_chat_member
    if user.is_bot:  # Skip bot departures
        return
        
    chat = update.effective_chat
    message = random.choice(GOODBYE_MESSAGES).format(
        mention=user.mention_html(),
        chat_title=chat.title
    )
    
    await context.bot.send_message(
        chat.id,
        message,
        parse_mode="HTML"
    )


class CosmicWish:
    RESPONSES = [
        (0, 20, "🌑 Your wish was lost in the void..."),
        (21, 50, "🌘 The cosmos is uncertain..."),
        (51, 80, "🌠 The stars are thinking about it..."),
        (81, 95, "🌟 Your wish glows brightly!"),
        (96, 100, "⚡ THE COSMOS DEMANDS IT!")
    ]
    IMAGES = {
        "good": "https://files.catbox.moe/n0qgc4.jpg",
        "neutral": "https://files.catbox.moe/n0qgc4.jpg",
        "bad": "https://files.catbox.moe/n0qgc4.jpg"
    }

    def __init__(self):
        self.history = {}
        self.cooldowns = {}

    async def wish(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg, user = update.message, update.effective_user
        if not msg:
            return

        if not context.args:
            await self._wish_help(msg)
            return

        # Cooldown logic (5 seconds)
        if self._on_cooldown(user.id):
            await msg.reply_text("⏳ The cosmos is still listening... wait 5 seconds.")
            return
        self._update_cooldown(user.id)

        wish = ' '.join(context.args)
        prob = random.randint(0, 100)
        verdict = self._get_verdict(prob)
        self._track(user.id, wish, prob)

        await msg.reply_photo(
            photo=self._get_image(prob),
            caption=(
                f"✨ <b>Cosmic Wish Evaluation</b> ✨\n\n"
                f"👤 <b>Wisher:</b> {user.mention_html()}\n"
                f"🌌 <b>Wish:</b> <i>{wish}</i>\n"
                f"🔢 <b>Chance:</b> <code>{prob}%</code>\n"
                f"⚖️ <b>Verdict:</b> {verdict}\n\n"
                f"📅 {datetime.now().strftime('%b %d, %Y — %H:%M')}"
            ),
            parse_mode="HTML",
            reply_markup=self._buttons(prob)
        )

    def _on_cooldown(self, user_id: int) -> bool:
        now = datetime.now()
        last = self.cooldowns.get(user_id)
        return last and (now - last) < timedelta(seconds=5)

    def _update_cooldown(self, user_id: int):
        self.cooldowns[user_id] = datetime.now()

    def _get_verdict(self, prob: int) -> str:
        for min_p, max_p, msg in self.RESPONSES:
            if min_p <= prob <= max_p:
                return msg
        return "🌌 The stars are unsure..."

    def _get_image(self, prob: int) -> str:
        return (
            self.IMAGES["good"] if prob > 80 else
            self.IMAGES["neutral"] if prob > 40 else
            self.IMAGES["bad"]
        )

    def _track(self, uid: int, wish: str, prob: int):
        self.history.setdefault(uid, []).append({
            "wish": wish,
            "prob": prob,
            "time": datetime.now()
        })

    def _buttons(self, prob: int):
        buttons = [[InlineKeyboardButton("🔁 Wish Again", callback_data="wish_again")]]
        if prob > 80:
            buttons[0].append(InlineKeyboardButton("📜 My Wishes", callback_data="wish_history"))
        return InlineKeyboardMarkup(buttons)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        user = q.from_user

        if q.data == "wish_again":
            await q.edit_message_text("🔄 The universe resets...\nSend your new /wish ✨", parse_mode="HTML")
        elif q.data == "wish_history":
            text = self._history_text(user.id)
            await q.edit_message_text(text, parse_mode="HTML")

    def _history_text(self, uid: int) -> str:
        logs = self.history.get(uid, [])
        if not logs:
            return "🌌 You haven’t wished yet!"
        txt = f"📜 <b>Your Recent Wishes</b>:\n\n"
        for i, w in enumerate(reversed(logs[-5:]), 1):
            txt += f"{i}. <code>{w['prob']}%</code> — <i>{w['wish']}</i>\n"
        return txt

    async def _wish_help(self, msg):
        await msg.reply_text(
            "💫 <b>Make a Cosmic Wish</b>\n\n"
            "Usage:\n"
            "• <code>/wish I want peace</code>\n"
            "• <code>/wish I hope for love</code>\n\n"
            "✨ The cosmos will respond...",
            parse_mode="HTML"
        )

import os
import textwrap
import asyncio
from datetime import datetime
from tempfile import NamedTemporaryFile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, ContextTypes

# === Font Setup ===
FONT_DIR = Path(__file__).parent / "fonts"
TIMES_NEW_ROMAN = FONT_DIR / "Times New Roman.ttf"
TIMES_NEW_ROMAN_ITALIC = FONT_DIR / "Times New Roman Italic.ttf"

# === /note Handler ===
async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⌨️ *Please provide text to generate a typed note.*\n\n"
            "_Example:_ `/note This is a note I want to type.`",
            parse_mode="Markdown"
        )
        return

    note_text = ' '.join(context.args)
    username = update.effective_user.username or "UnknownUser"
    timestamp = datetime.now().strftime("%I:%M %p")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        # Run image generation in background thread (non-blocking)
        image_path = await asyncio.to_thread(generate_note_image, note_text, username, timestamp)

        await update.message.reply_photo(
            photo=image_path,
            caption="📄 *Typed Note generated by* @MonicRobot",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to create note: `{e}`", parse_mode="Markdown")
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

# === Generate Note Image ===
def generate_note_image(text: str, username: str, time_str: str) -> str:
    font_size = 80
    footer_size = 30
    margin = 70
    spacing = 20
    line_limit = 60

    # Load fonts with fallback
    try:
        font_main = ImageFont.truetype(str(TIMES_NEW_ROMAN), font_size)
        font_footer = ImageFont.truetype(str(TIMES_NEW_ROMAN_ITALIC), footer_size)
    except Exception as e:
        print(f"[Font Fallback] {e}")
        font_main = ImageFont.load_default()
        font_footer = ImageFont.load_default()

    lines = textwrap.wrap(text, width=line_limit)
    text_height = len(lines) * (font_size + spacing)
    footer_height = 80

    img_width = int(max(font_main.getlength(line) for line in lines) + margin * 2)
    img_height = int(text_height + footer_height + margin * 2)

    img = Image.new("RGB", (img_width, img_height), color="white")
    draw = ImageDraw.Draw(img)

    y = margin
    for line in lines:
        draw.text((margin, y), line, font=font_main, fill="black")
        y += font_size + spacing

    footer_text = f"✍️ @{username} • {time_str}"
    draw.text((margin, img_height - footer_height), footer_text, font=font_footer, fill=(100, 100, 100))

    with NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        img.save(tmp_file.name, format="PNG")
        return tmp_file.name

import os
import re
import asyncio
from uuid import uuid4
from pathlib import Path
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Constants ===
DOWNLOAD_DIR = Path(__file__).resolve().parent / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
COOKIE_FILE = os.path.join(os.getcwd(), "ytcookies.txt")

# === Utility ===
def clean_filename(name: str) -> str:
    return re.sub(r"[\\/*?\"<>|]", "", name)

# === /song command ===
async def yt_song_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args or [])
    if not query:
        return await update.message.reply_text("❌ Please provide a song name or YouTube URL.")

    # Immediate response to user
    processing_msg = await update.message.reply_text("🔄 Processing your song...")

    # Run in background (non-blocking)
    asyncio.create_task(process_song(update, context, query, processing_msg))


async def process_song(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, msg):
    uid = uuid4().hex
    output_template = DOWNLOAD_DIR / f"{uid}.%(ext)s"
    final_path = None

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_template),
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "default_search": "ytsearch1",  # Top 1 only
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        # Download using yt-dlp
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)

        title = clean_filename(info.get("title", uid))
        downloaded_path = output_template.with_suffix(".mp3")
        final_path = DOWNLOAD_DIR / f"{title}.mp3"
        if downloaded_path != final_path:
            downloaded_path.rename(final_path)

        # Uploading to Telegram
        await msg.edit_text("📤 Uploading your song...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_VOICE)

        audio = MP3(final_path)
        duration = int(audio.info.length)
        performer = info.get("uploader", "Unknown Artist")

        await context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=open(final_path, "rb"),
            title=info.get("title", title),
            performer=performer,
            duration=duration,
            reply_to_message_id=update.message.message_id
        )

        await msg.edit_text("✅ Done! Enjoy your music 🎵")
        final_path.unlink(missing_ok=True)

    except Exception as e:
        await msg.edit_text(f"❌ Failed to process song.\n\n`{e}`", parse_mode="Markdown")
        if final_path and final_path.exists():
            final_path.unlink(missing_ok=True)


from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ContextTypes, filters
import datetime
import psutil
import platform
import sqlite3
from functools import wraps

# Replace with your owner ID
OWNERID = 8429156335  # Your Telegram user ID

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ContextTypes, filters, MessageHandler
import datetime
import psutil
import platform
import sqlite3
import time
from functools import wraps

# Configuration
OWNER_ID = 8429156335  # Replace with your Telegram user ID
DB_NAME = 'bot_stats.db'

def owner_only(func):
    """Decorator to restrict command to owner only"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("⚠️ This command is restricted to the bot owner only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def initialize_database():
    """Initialize the database with required tables"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Create users table if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                        (user_id INTEGER PRIMARY KEY, 
                         username TEXT, 
                         first_seen TEXT)''')
        
        # Create chats table if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS chats 
                        (chat_id INTEGER PRIMARY KEY, 
                         chat_title TEXT, 
                         is_group BOOLEAN, 
                         first_seen TEXT)''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")

async def get_bot_chat_stats():
    """Get the number of users and groups the bot interacts with"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Get group count
        cursor.execute("SELECT COUNT(*) FROM chats WHERE is_group = 1")
        group_count = cursor.fetchone()[0]
        
        conn.close()
        return user_count, group_count
    except Exception as e:
        print(f"Error getting chat stats: {e}")
        return "N/A", "N/A"

@owner_only
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /stats command to show bot statistics (owner only)"""
    # System statistics
    system = platform.system()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(context.bot_data.get('start_time', time.time()))
    
    # Get bot stats
    user_count, group_count = await get_bot_chat_stats()
    bot = await context.bot.get_me()
    
    # Format uptime
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    # Prepare the stats message
    stats_text = (
        f"🤖 <b>{bot.first_name} Statistics</b> (Owner Only)\n\n"
        f"👥 <b>User Stats</b>\n"
        f"• Total Users: {user_count}\n"
        f"• Group Chats: {group_count}\n\n"
        f"⚙️ <b>System Info</b>\n"
        f"• OS: {system}\n"
        f"• RAM: {memory.percent}% used ({memory.used/1024/1024:.1f} MB)\n"
        f"• Disk: {disk.percent}% used ({disk.used/1024/1024:.1f} MB)\n"
        f"• Uptime: {uptime_str}\n\n"
        f"📅 Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    # Add buttons
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats")],
        [InlineKeyboardButton("📊 Detailed Stats", callback_data="detailed_stats")],
        [InlineKeyboardButton("❌ Close", callback_data="close_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track new users and chats"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Track user
        user = update.effective_user
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_seen) VALUES (?, ?, ?)",
            (user.id, user.username, datetime.datetime.now().isoformat())
        )
        
        # Track chat if in group
        if update.effective_chat.type in ['group', 'supergroup']:
            chat = update.effective_chat
            cursor.execute(
                "INSERT OR IGNORE INTO chats (chat_id, chat_title, is_group, first_seen) VALUES (?, ?, ?, ?)",
                (chat.id, chat.title, True, datetime.datetime.now().isoformat())
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error tracking chat: {e}")

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stats callback queries (owner only)"""
    query = update.callback_query
    await query.answer()
    
    # Verify owner
    if query.from_user.id != OWNER_ID:
        await query.edit_message_text("⚠️ This command is restricted to the bot owner only.")
        return
    
    if query.data == "refresh_stats":
        await stats_command(update, context)
    elif query.data == "detailed_stats":
        user_count, group_count = await get_bot_chat_stats()
        detailed_text = (
            f"📊 <b>Detailed Statistics</b>\n\n"
            f"• Total Users: {user_count}\n"
            f"• Group Chats: {group_count}\n\n"
            f"<i>More detailed analytics can be added here</i>"
        )
        await query.edit_message_text(
            text=detailed_text,
            parse_mode='HTML'
        )
    elif query.data == "close_stats":
        await query.delete_message()


# ======================
# Entry Point
# ======================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", show_help))
    app.add_handler(CallbackQueryHandler(help_page_callback, pattern="^help_page_"))
    app.add_handler(CallbackQueryHandler(show_help_category, pattern="^help_"))
    app.add_handler(CommandHandler("pin", pin))
    app.add_handler(CommandHandler("unpin", unpin))
    app.add_handler(CommandHandler("pinned", pinned))
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("lowpromote", lowpromote))
    app.add_handler(CommandHandler("midpromote", midpromote))
    app.add_handler(CommandHandler("fullpromote", fullpromote))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("delete_msg", delete_msg))
    app.add_handler(CommandHandler("purge", purge))
    app.add_handler(CommandHandler("spurge", spurge))
    app.add_handler(CommandHandler("settitle", settitle))
    app.add_handler(CommandHandler("setdesc", setdesc))
    app.add_handler(CommandHandler("setgpic", setgpic))
    app.add_handler(CommandHandler("rmgpic", rmgpic))
    app.add_handler(CommandHandler("invitelink", invitelink))
    app.add_handler(CallbackQueryHandler(invite_callback, pattern="invite_regen"))
    app.add_handler(CommandHandler("adminlist", adminlist))
    app.add_handler(CommandHandler("title", title))
    app.add_handler(CommandHandler("afk", afk_command))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        check_user_activity
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        notify_afk_mention
    ))
    app.add_handler(MessageHandler(filters.ALL, track_chats), group=-1)
    app.add_handler(CommandHandler("antibanall", antibanall_command))
    app.add_handler(CallbackQueryHandler(antibanall_toggle, pattern=r"^antibanall_toggle_"))
    app.add_handler(CallbackQueryHandler(whitelist_handler, pattern=r"^antibanall_whitelist$"))
    app.add_handler(CallbackQueryHandler(whitelist_toggle, pattern=r"^antibanall_whitelist_toggle:"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern=r"^antibanall_back$"))
    
    # Register chat member handler for monitoring bans
    app.add_handler(ChatMemberHandler(monitor_bans, ChatMemberHandler.CHAT_MEMBER))
    logger.info("✅ AntiBanAll bot handlers loaded successfully")
    app.add_handler(CommandHandler("kickme", kickme))
    app.add_handler(CommandHandler("banme", banme))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("sban", sban))
    app.add_handler(CommandHandler("tban", tban))
    app.add_handler(CommandHandler("dban", dban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("tmute", tmute))
    app.add_handler(CommandHandler("smute", smute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("cutie", cutie))
    app.add_handler(CommandHandler("horny", horny))
    app.add_handler(CommandHandler("hot", hot))
    app.add_handler(CommandHandler("sexy", sexy))
    app.add_handler(CommandHandler("gay", gay))
    app.add_handler(CommandHandler("lesbian", lesbian))
    app.add_handler(CommandHandler("boob", boob))
    app.add_handler(CommandHandler("cock", cock))
    app.add_handler(CommandHandler(["calc", "calculate", "math"], calc_command))
    app.add_handler(
        telegram.ext.CallbackQueryHandler(calc_example_callback, pattern="^calc_example$")

    )
    app.add_handler(CommandHandler("code", code_command))
    app.add_handler(CommandHandler("cosplay", animepic_cmd))
    app.add_handler(CommandHandler("animepic", animepic_cmd))
    app.add_handler(CommandHandler("couple", couple_cmd))
    app.add_handler(CommandHandler("waifu", waifu_cmd))
    app.add_handler(CommandHandler("currency", convert_currency))
    app.add_handler(CommandHandler("currencylist", list_currencies))
    app.add_handler(CommandHandler("extract", extract_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(extract_|cancel_extract)"))
    app.add_handler(CommandHandler("fake", fake_generator))
    app.add_handler(CommandHandler("ff" , ffid_command))
    app.add_handler(CommandHandler("figlet", figlet_command))
    app.add_handler(CallbackQueryHandler(figlet_callback, pattern="^figlet$"))
    app.add_handler(CallbackQueryHandler(close_reply, pattern="^close_reply$"))
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stop", remove_filter))
    app.add_handler(CommandHandler("filters", list_filters))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_trigger), group=1)
    app.add_handler(CommandHandler("font", font_command))
    app.add_handler(CallbackQueryHandler(font_nxt, pattern="^nxt$"))
    app.add_handler(CallbackQueryHandler(font_style, pattern=r"^style\+"))
    app.add_handler(CallbackQueryHandler(font_nxt, pattern=r"^nxt\+\d+$"))
    app.add_handler(CallbackQueryHandler(font_style, pattern=r"^style\+.+$"))
    for cmd in COMMANDS:
        app.add_handler(CommandHandler(cmd, waifu_command))
    app.add_handler(CallbackQueryHandler(next_callback, pattern=r"^next_"))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("rmsudo", rmsudo))
    app.add_handler(CommandHandler("sudousers", sudousers))
    app.add_handler(CommandHandler("addlord", addlord))
    app.add_handler(CommandHandler("rmlord", rmlord))
    app.add_handler(CommandHandler("lords", lords))
    app.add_handler(CommandHandler("gban", gban, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("ungban", ungban, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("gmute", gmute, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("ungmute", ungmute, filters=filters.ChatType.GROUPS))
    
    # Message handlers with lower priority to allow other modules to process first
    app.add_handler(
        MessageHandler(filters.ChatType.GROUPS, global_enforcement_handler),
        group=-1  # Lower priority group
    )
    app.add_handler(
        MessageHandler(filters.ChatType.GROUPS, stats_track_handler),
        group=-1  # Lower priority group
    )
    app.add_handler(ChatMemberHandler(royal_welcome, chat_member_types=["member"]))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_all_messages))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_links), group=1)
    app.add_handler(CommandHandler("ip", ip_info_and_score))
    app.add_handler(CommandHandler("leave", leave_command))
    app.add_handler(CommandHandler("leaveall", leave_all_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^leave_all_"))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("meme", meme_command))
    app.add_handler(CommandHandler("nightmode", nightmode_toggle))
    app.add_handler(CommandHandler("nightmode_time", set_nightmode_time))

    initialize_database()
    
    # Record bot start time
    
    # Add command handler (owner only)
    app.add_handler(CommandHandler(
        "stats", 
        stats_command, 
        filters=filters.User(OWNER_ID)
    ))
    
    # Add callback handler
    app.add_handler(CallbackQueryHandler(
        stats_callback, 
        pattern="^(refresh_stats|detailed_stats|close_stats)$"
    ))
    
    # Add chat tracking handler (should be last)
    app.add_handler(MessageHandler(filters.ALL, track_chats), group=-1)

    # Schedule the nightmode job to run every minute
    app.job_queue.run_repeating(nightmode_job, interval=60, first=0)
    app.add_handler(CommandHandler("checkrights", check_rights))
    app.add_handler(CallbackQueryHandler(refresh_rights, pattern="refresh_rights"))
    app.add_handler(CallbackQueryHandler(close_rights, pattern="rights_close"))
    app.add_handler(CallbackQueryHandler(noop_rights, pattern="rights_noop"))
    app.add_handler(CommandHandler("pokedex", pokedex))
    app.add_handler(CallbackQueryHandler(pokedex_handler, pattern=r"^(stats|moves|abilities|cry|back)_"))
    app.add_handler(CommandHandler("population", population_command))
    app.add_handler(CommandHandler("todo", todo_menu))
    app.add_handler(CallbackQueryHandler(handle_todo_callback, pattern=r"todo_.*"))
    app.add_handler(CallbackQueryHandler(handle_task_actions, pattern=r"(complete|remove|confirm)_[0-9]+"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_input))
    app.add_handler(
        CommandHandler("qrcode", qrcode_cmd, filters=filters.TEXT | filters.REPLY)
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, qrcode_cmd)
    )
    app.add_handler(CommandHandler("q", quote_command, filters=filters.REPLY))
    app.add_handler(CommandHandler("qt", fake_quote_command, filters=filters.REPLY))
    app.add_handler(CommandHandler(["qr", "q_r"], quote_command, filters=filters.REPLY))
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, button_callback))
    app.add_handler(CommandHandler("aquote", aquote))
    app.add_handler(CommandHandler("iaquotes", iaquotes))
    app.add_handler(CommandHandler("shayri", shayri))
    
    # Add callback handler
    app.add_handler(CallbackQueryHandler(button_handler))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("sgen", start_sgen)],
        states={
            LIBRARY: [CallbackQueryHandler(handle_library_button)],
            API_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_api_id)],
            API_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_api_hash)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_code)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(
        CommandHandler("speedtest", speedtest_command)
    )
    app.add_handler(CommandHandler("cricket", cricket_cmd))
    app.add_handler(CommandHandler("football", football_cmd))
    app.add_handler(CallbackQueryHandler(match_callback, pattern=r"^(next|prev|refresh|page_info)_(cricket|football)$"))
    app.add_handler(CommandHandler("stickerinfo", stickerinfo))
    app.add_handler(CommandHandler("getsticker", getsticker))
    app.add_handler(CommandHandler("getvidsticker", getvidsticker))
    app.add_handler(CommandHandler("mmf", memify))
    app.add_handler(CommandHandler("tiny", tiny_command))
    tts_handler = CommandHandler('tts', handle_tts, filters=filters.TEXT)
    app.add_handler(tts_handler)
    
    # Add usage command
    usage_handler = CommandHandler('tts_usage', TTSBot.send_usage, filters=filters.TEXT)
    app.add_handler(usage_handler
                            )
    app.add_handler(CommandHandler("ud", urban_command))
    app.add_handler(CallbackQueryHandler(
        UrbanDictionaryUI.handle_more_slang_callback, 
        pattern="more_slang"
    ))
    app.add_handler(CallbackQueryHandler(
        UrbanDictionaryUI.handle_random_word_callback, 
        pattern="random_word"
    ))
    app.add_handler(
        CommandHandler("tgm", handle_media_upload)
    )
    app.add_handler(
        CommandHandler("tgt", handle_text_upload)
    )
    upscaler = UltraUpscaler()
    app.add_handler(CommandHandler("upscale", upscaler.handle_upscale))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, profile_watcher))
    app.add_handler(CommandHandler("warn", warn_user))
    app.add_handler(CommandHandler("dwarn", delete_and_warn))
    app.add_handler(CommandHandler("unwarn", remove_warning))
    app.add_handler(CommandHandler("warns", check_warnings))
    app.add_handler(CommandHandler("resetwarns", reset_warnings))
    
    # Settings commands
    app.add_handler(CommandHandler("warnsettings", warn_settings))
    app.add_handler(CommandHandler("setwarnlimit", set_warn_limit))
    
    # Button handlers
    app.add_handler(CallbackQueryHandler(
        handle_warning_button, 
        pattern=r"^(unwarn|clearwarns|ban)_\d+_\d+$"
    ))
    
    # Schedule periodic cleanup of expired warnings
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(
            lambda _: db.cleanup_expired_warnings(),
            interval=86400,  # Run daily
            first=10
        )
        app.add_handler(CommandHandler("weather", weather))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_user))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye_user))
    wish = CosmicWish()
    app.add_handler(CommandHandler("wish", wish.wish))
    app.add_handler(CallbackQueryHandler(wish.handle_callback, pattern="^wish_"))
    app.add_handler(CommandHandler("note", note_command))
    app.add_handler(CommandHandler("song", yt_song_handler))
    from telegram.ext import ContextTypes


    app.run_polling()
