import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
)
from deep_translator import GoogleTranslator

# --- ENVIRONMENT CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
ADMIN_ID = 7559409737  # Omar

# --- CHANNEL ROUTING ---
CHANNEL_MAP = {
    -1003745031724: -1003820544434,  # Golden"HardScalping"Room → SCALPING JZ GOLD
    -1003189185116: -1003912710963,  # Golden"Daytrading"Room → DAYTRADING JZ GOLD
}

# --- NAMES TO REPLACE ---
NAMES_TO_REPLACE = [
    (r"Analisis Heury,?\s*Elián\s*y\s*Jafet\s*[🧠📊🔠]*\s*", "Analisis Manuel Jimenez "),
    (r"Analisis Heury,?\s*", "Analisis Manuel Jimenez "),
    (r"Elián\s*y\s*Jafet\s*", ""),
    (r"Elián\s*", ""),
    (r"Jafet\s*", ""),
    (r"Heury\s*", ""),
]

# --- CHANNEL/BRAND NAMES TO REMOVE ---
NAMES_TO_REMOVE = [
    r"Golden\s*\"?HardScalping\"?\s*Room\s*",
    r"Golden\s*\"?Daytrading\"?\s*Room\s*",
    r"SCALPING JZ\s*💸?\s*GOLD\s*🌿?\s*",
    r"DAYTRADING JZ\s*💰?\s*GOLD\s*🌿?\s*",
    r"SCALPING JZ\s*🦅?\s*GOLD\s*🏆?\s*",
    r"SCALPING JZ\s*",
    r"DAYTRADING JZ\s*",
    r"BlockSavvyMxQ\s*",
    r"MyForexSignals\s*",
    r"HARDSCALPING\s*",
    r"Los Visionarios\s*",
    r"LOS VISIONARIOS\s*",
    r"Visionarios\s*",
]

# --- WORD REPLACEMENTS ---
WORD_REPLACEMENTS = {
    r"VENDER": "SELL",
    r"COMPRAR": "BUY",
    r"Vende\b": "SELL",
    r"Compra\b": "BUY",
}

# --- IMAGES TO BLOCK (based on caption text) ---
BLOCKED_IMAGE_PHRASES = [
    r"los visionarios",
    r"visionarios",
    r"cuánto habrías ganado",
    r"cuanto habrias ganado",
    r"pips netos",
    r"resultado semanal",
    r"resultado acumulado",
    r"resultado.*tabla",
    r"ganancia.*capital",
    r"capital.*usd",
    r"solo entrada",
    r"lunes.*martes.*miercoles",
    r"lunes.*martes.*miércoles",
    r"day trading.*oro",
    r"rendimiento diario",
    r"rendimiento del canal",
    r"beneficio neto",
    r"tasa de ganancia",
    r"reporte",
    r"resultado",
    r"canal vip",
    r"participantes",
    r"review",
    r"testimonial",
    r"subscribe",
    r"suscri",
    r"join",
    r"únete",
    r"promotion",
    r"promo",
]

# --- VALID MESSAGES TO COPY ---
ALLOWED_PATTERNS = [
    r"señal lista",
    r"pendientes",
    r"vender\b",
    r"comprar\b",
    r"sell\b",
    r"buy\b",
    r"entrar entre",
    r"entry",
    r"entrada",
    r"xauusd",
    r"eurusd",
    r"gbpusd",
    r"usdjpy",
    r"\bsl\b",
    r"stop loss",
    r"\btp1\b",
    r"\btp2\b",
    r"\btp3\b",
    r"\btp4\b",
    r"\btp\s*\d\b",
    r"take profit",
    r"asegura",
    r"secure",
    r"todo en break",
    r"break even",
    r"breakeven",
    r"break en",
    r"colocar break",
    r"coloquen break",
    r"place break",
    r"poner break",
    r"mover break",
    r"están en break",
    r"en break",
    r"50%",
    r"ganancias",
    r"pagando",
    r"dentro\b",
    r"seguimos",
    r"cierra",
    r"razón para",
    r"razon para",
    r"patrón",
    r"patron",
    r"engulfing",
    r"base de",
    r"alcanzado",
    r"invalidada",
    r"retroceso",
    r"tp.*abierto",
    r"corriendo",
    r"colocar",
    r"coloquen",
    r"que rico",
    r"desde el mejor precio",
    r"super entrada",
    r"hit tp",
]

# --- SYSTEM VARIABLES ---
SETTINGS = {
    "ai_translate": False,
    "target_language": "en",
    "paused": False,
    "custom_replacements": {},
    "blocked_words": [],
}

LANGUAGES = {
    "🇬🇧 English": "en",
    "🇪🇸 Spanish": "es",
    "🇫🇷 French": "fr",
    "🇩🇪 German": "de",
    "🇧🇷 Portuguese": "pt",
    "🇸🇦 Arabic": "ar",
    "🇨🇳 Chinese": "zh",
    "🇷🇺 Russian": "ru",
    "🇮🇹 Italian": "it",
}

print("Starting Omar Channel Replicator Bot...")

user_client = TelegramClient(
    StringSession(SESSION_STRING), API_ID, API_HASH
)
bot_client = TelegramClient(StringSession(), API_ID, API_HASH)


def is_authorized(sender_id):
    return sender_id in [OWNER_ID, ADMIN_ID]


def is_audio_message(message):
    if not message.media:
        return False
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if hasattr(doc, 'mime_type') and doc.mime_type:
            if doc.mime_type.startswith('audio/'):
                return True
        if hasattr(doc, 'attributes'):
            for attr in doc.attributes:
                if type(attr).__name__ in [
                    'DocumentAttributeAudio',
                    'DocumentAttributeVoice'
                ]:
                    return True
    return False


def is_video_message(message):
    if not message.media:
        return False
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if hasattr(doc, 'mime_type') and doc.mime_type:
            if doc.mime_type.startswith('video/'):
                return True
        if hasattr(doc, 'attributes'):
            for attr in doc.attributes:
                if type(attr).__name__ == 'DocumentAttributeVideo':
                    return True
    return False


def is_photo_message(message):
    return isinstance(message.media, MessageMediaPhoto)


def is_blocked_image(text):
    """Block images with certain phrases in caption."""
    if not text:
        return False
    for phrase in BLOCKED_IMAGE_PHRASES:
        if re.search(phrase, text, re.IGNORECASE):
            print(f"🚫 Blocked image phrase: {phrase}")
            return True
    return False


def is_allowed_message(text):
    """Check if message contains valid trading content."""
    if not text:
        return False
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def is_blocked_word_found(text):
    if not text:
        return False
    for word in SETTINGS["blocked_words"]:
        if word.lower() in text.lower():
            return True
    return False


def has_links(text):
    if not text:
        return False
    return bool(re.search(
        r'https?://\S+|t\.me/\S+|www\.\S+',
        text, re.IGNORECASE
    ))


def clean_message(text):
    """Remove names, links, handles and normalize."""
    if not text:
        return text
    # Replace person names
    for pattern, replacement in NAMES_TO_REPLACE:
        text = re.sub(
            pattern, replacement, text, flags=re.IGNORECASE
        )
    # Remove channel/brand names
    for pattern in NAMES_TO_REMOVE:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    # Remove @usernames and links
    text = re.sub(r'@\w+', '', text)
    text = re.sub(
        r'https?://\S+|t\.me/\S+|www\.\S+', '', text
    )
    # Apply word replacements
    for pattern, replacement in WORD_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text)
    # Apply custom replacements
    for old, new in SETTINGS["custom_replacements"].items():
        text = re.sub(
            re.escape(old), new, text, flags=re.IGNORECASE
        )
    # Translate if enabled
    if SETTINGS["ai_translate"] and text:
        try:
            translated = GoogleTranslator(
                source='auto',
                target=SETTINGS["target_language"]
            ).translate(text)
            if translated:
                text = translated
        except Exception as e:
            print(f"Translation error: {e}")
    # Clean up blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def get_main_menu_buttons():
    translate_status = (
        "✅ ON" if SETTINGS["ai_translate"] else "🛑 OFF"
    )
    pause_label = (
        "▶️ Resume" if SETTINGS["paused"] else "⏸ Pause"
    )
    return [
        [events.Button.inline(
            f"🌐 Translation: {translate_status}",
            "toggle_translate"
        )],
        [events.Button.inline("🗣 Change Language", "change_language")],
        [events.Button.inline(pause_label, "toggle_pause")],
        [events.Button.inline("📊 Status", "show_status")],
        [events.Button.inline("📡 Channels", "show_channels")],
        [events.Button.inline("❌ Close", "close")],
    ]


async def safe_edit(event, text, buttons=None):
    try:
        if buttons:
            await event.edit(text, buttons=buttons)
        else:
            await event.edit(text)
    except Exception as e:
        if "not modified" in str(e).lower():
            pass
        else:
            print(f"Edit error: {e}")


# -------------------------------------------------------------------
# COMMAND HANDLER
# -------------------------------------------------------------------
@bot_client.on(events.NewMessage(pattern=r'^/'))
async def command_menu(event):
    if not is_authorized(event.sender_id):
        return

    command = event.text.strip().lower()
    full_text = event.text.strip()

    if command == "/start":
        await event.respond(
            "⚙️ **Channel Replicator Control Panel**\n\n"
            "Commands:\n"
            "➡️ `/ai on` - Enable translation\n"
            "➡️ `/ai off` - Disable translation (default)\n"
            "➡️ `/status` - Check current bot status\n"
            "➡️ `/pause` - Pause copying\n"
            "➡️ `/resume` - Resume copying\n"
            "➡️ `/help` - All commands"
        )

    elif command == "/help":
        await event.respond(
            "📋 **Available Commands:**\n\n"
            "**🔧 System:**\n"
            "➡️ `/start` - Welcome message\n"
            "➡️ `/help` - Show all commands\n"
            "➡️ `/status` - Current bot status\n\n"
            "**⏯ Control:**\n"
            "➡️ `/pause` - Pause all copying\n"
            "➡️ `/resume` - Resume copying\n\n"
            "**🌐 Translation:**\n"
            "➡️ `/ai on` - Enable translation\n"
            "➡️ `/ai off` - Disable translation\n"
            "➡️ `/language en` - English\n"
            "➡️ `/language es` - Spanish\n"
            "➡️ `/language fr` - French\n\n"
            "**✏️ Word Management:**\n"
            "➡️ `/addword old:new` - Replace a word\n"
            "➡️ `/removeword word` - Remove replacement\n"
            "➡️ `/wordlist` - Show replacements\n"
            "➡️ `/blockword word` - Block a word\n"
            "➡️ `/unblockword word` - Unblock a word\n"
            "➡️ `/blocklist` - Show blocked words\n\n"
            "**📡 Channels:**\n"
            "➡️ `/channels` - Show channel routing\n"
        )

    elif command == "/status":
        paused = "⏸ PAUSED" if SETTINGS["paused"] else "▶️ RUNNING"
        translate = "✅ ON" if SETTINGS["ai_translate"] else "🛑 OFF"
        lang_name = next(
            (k for k, v in LANGUAGES.items()
             if v == SETTINGS["target_language"]),
            SETTINGS["target_language"]
        )
        await event.respond(
            f"📊 **Current System Status:**\n\n"
            f"• Bot State: `{paused}`\n"
            f"• Translation: `{translate}`\n"
            f"• Language: `{lang_name}`\n"
            f"• Custom Replacements: "
            f"`{len(SETTINGS['custom_replacements'])}`\n"
            f"• Blocked Words: "
            f"`{len(SETTINGS['blocked_words'])}`\n\n"
            f"📡 **Routing:**\n"
            f"• HardScalping Room → SCALPING JZ GOLD\n"
            f"• Daytrading Room → DAYTRADING JZ GOLD"
        )

    elif command == "/pause":
        SETTINGS["paused"] = True
        await event.respond(
            "⏸ **Bot Paused.**\n"
            "Send /resume to restart copying."
        )

    elif command == "/resume":
        SETTINGS["paused"] = False
        await event.respond(
            "▶️ **Bot Resumed.**\n"
            "Copying signals again."
        )

    elif command == "/ai on":
        SETTINGS["ai_translate"] = True
        lang_name = next(
            (k for k, v in LANGUAGES.items()
             if v == SETTINGS["target_language"]),
            SETTINGS["target_language"]
        )
        await event.respond(
            f"✅ **Translation ON** → `{lang_name}`"
        )

    elif command == "/ai off":
        SETTINGS["ai_translate"] = False
        await event.respond(
            "🛑 **Translation OFF.**\n"
            "Messages keep original language."
        )

    elif command.startswith("/language "):
        lang = command.split("/language ")[1].strip()
        if lang in LANGUAGES.values():
            SETTINGS["target_language"] = lang
            lang_name = next(
                (k for k, v in LANGUAGES.items() if v == lang),
                lang
            )
            await event.respond(
                f"🌐 **Language set to {lang_name}**"
            )
        else:
            await event.respond(
                f"❌ Unsupported: `{lang}`\n"
                f"Try: en, es, fr, de, pt"
            )

    elif full_text.lower().startswith("/addword "):
        try:
            parts = full_text[9:].split(":")
            if len(parts) == 2:
                old_word = parts[0].strip()
                new_word = parts[1].strip()
                SETTINGS["custom_replacements"][old_word] = new_word
                await event.respond(
                    f"✅ **Added:** `{old_word}` → `{new_word}`"
                )
            else:
                await event.respond(
                    "❌ Use: `/addword oldword:newword`"
                )
        except Exception:
            await event.respond(
                "❌ Use: `/addword oldword:newword`"
            )

    elif full_text.lower().startswith("/removeword "):
        word = full_text[12:].strip()
        if word in SETTINGS["custom_replacements"]:
            del SETTINGS["custom_replacements"][word]
            await event.respond(f"✅ **Removed:** `{word}`")
        else:
            await event.respond(f"❌ `{word}` not found.")

    elif command == "/wordlist":
        if SETTINGS["custom_replacements"]:
            replacements = "\n".join(
                [f"• `{k}` → `{v}`"
                 for k, v in SETTINGS[
                     "custom_replacements"
                 ].items()]
            )
            await event.respond(
                f"📝 **Replacements:**\n\n{replacements}"
            )
        else:
            await event.respond(
                "📝 None yet. Use `/addword old:new`"
            )

    elif full_text.lower().startswith("/blockword "):
        word = full_text[11:].strip()
        if word not in SETTINGS["blocked_words"]:
            SETTINGS["blocked_words"].append(word)
            await event.respond(f"🚫 **Blocked:** `{word}`")
        else:
            await event.respond(f"⚠️ Already blocked.")

    elif full_text.lower().startswith("/unblockword "):
        word = full_text[13:].strip()
        if word in SETTINGS["blocked_words"]:
            SETTINGS["blocked_words"].remove(word)
            await event.respond(f"✅ **Unblocked:** `{word}`")
        else:
            await event.respond(f"❌ Not in blocked list.")

    elif command == "/blocklist":
        if SETTINGS["blocked_words"]:
            words = "\n".join(
                [f"• `{w}`" for w in SETTINGS["blocked_words"]]
            )
            await event.respond(
                f"🚫 **Blocked Words:**\n\n{words}"
            )
        else:
            await event.respond(
                "✅ None. Use `/blockword word`"
            )

    elif command == "/channels":
        await event.respond(
            "📡 **Channel Routing:**\n\n"
            "**Source 1:** Golden\"HardScalping\"Room\n"
            "**Destination 1:** SCALPING JZ GOLD\n\n"
            "**Source 2:** Golden\"Daytrading\"Room\n"
            "**Destination 2:** DAYTRADING JZ GOLD"
        )


# -------------------------------------------------------------------
# ALBUM HANDLER
# -------------------------------------------------------------------
@user_client.on(events.Album(chats=list(CHANNEL_MAP.keys())))
async def album_handler(event):
    if SETTINGS["paused"]:
        return

    source_id = event.chat_id
    destination_id = CHANNEL_MAP.get(source_id)
    if not destination_id:
        return

    # Skip audio/video
    for msg in event.messages:
        if is_audio_message(msg) or is_video_message(msg):
            print("⏭️ Skipped album: audio/video")
            return

    # Must have valid signal caption
    caption = None
    has_valid_caption = False
    for msg in event.messages:
        if msg.message:
            raw = msg.message
            # Block Visionarios and other unwanted images
            if is_blocked_image(raw):
                print("⏭️ Skipped album: blocked image")
                return
            if is_allowed_message(raw):
                has_valid_caption = True
                caption = clean_message(raw)
                break

    # Block albums with no valid signal caption
    if not has_valid_caption:
        print("⏭️ Skipped album: no valid signal caption")
        return

    # Only copy photos
    media_files = [
        msg.media for msg in event.messages
        if is_photo_message(msg)
    ]

    if media_files:
        try:
            await user_client.send_file(
                destination_id,
                media_files,
                caption=caption
            )
            print(f"✅ Album sent → {destination_id}")
        except Exception as e:
            print(f"❌ Album failed: {e}")


# -------------------------------------------------------------------
# SINGLE MESSAGE HANDLER
# -------------------------------------------------------------------
@user_client.on(events.NewMessage(chats=list(CHANNEL_MAP.keys())))
async def replication_engine(event):
    if SETTINGS["paused"]:
        return

    source_id = event.chat_id
    destination_id = CHANNEL_MAP.get(source_id)
    if not destination_id:
        return

    if event.message.grouped_id:
        return

    if is_audio_message(event.message):
        print("⏭️ Skipped: audio")
        return

    if is_video_message(event.message):
        print("⏭️ Skipped: video")
        return

    raw_text = event.message.message
    has_media = event.message.media is not None
    is_photo = is_photo_message(event.message)

    if not raw_text and not has_media:
        return

    # --- STRICT PHOTO FILTERING ---
    if is_photo:
        # Block photos with no caption completely
        # (Visionarios images have no caption)
        if not raw_text:
            print("⏭️ Skipped: photo with no caption")
            return
        # Block photos with blocked image phrases in caption
        if is_blocked_image(raw_text):
            print("⏭️ Skipped: blocked image phrase")
            return
        # Only allow photos with valid signal captions
        if not is_allowed_message(raw_text):
            print("⏭️ Skipped: photo not a valid signal")
            return

    # --- TEXT ONLY FILTERING ---
    if not has_media:
        if not raw_text:
            return
        if not is_allowed_message(raw_text):
            print("⏭️ Skipped: not allowed message")
            return
        if has_links(raw_text):
            print("⏭️ Skipped: has links")
            return
        if is_blocked_word_found(raw_text):
            print("⏭️ Skipped: blocked word")
            return

    # --- PROCESS AND SEND ---
    final_text = clean_message(raw_text) if raw_text else None

    try:
        if is_photo:
            await user_client.send_file(
                destination_id,
                event.message.media,
                caption=final_text
            )
        else:
            if not final_text:
                return
            await user_client.send_message(
                destination_id,
                final_text
            )
        print(f"✅ Mirrored: {source_id} → {destination_id}")
    except Exception as e:
        print(f"❌ Delivery failed: {e}")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
async def main():
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("❌ ERROR: Session string invalid or expired!")
        return
    print("✅ Userbot (scraper) is live.")

    await bot_client.start(bot_token=BOT_TOKEN)
    print("✅ Bot control panel is live.")

    print("🚀 Omar Channel Replicator Bot RUNNING!")
    print("📡 Golden\"HardScalping\"Room → SCALPING JZ GOLD")
    print("📡 Golden\"Daytrading\"Room → DAYTRADING JZ GOLD")
    print("🚫 Visionarios images: BLOCKED")

    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )


asyncio.run(main())
