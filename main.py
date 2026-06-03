import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from deep_translator import GoogleTranslator

# --- ENVIRONMENT CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
ADMIN_ID = 7559409737  # Omar's Telegram ID

# --- CHANNEL ROUTING ---
CHANNEL_MAP = {
    -1003745031724: -1003820544434,
    -1003189185116: -1003912710963,
}

# --- NAMES TO REPLACE ---
NAMES_TO_REPLACE = [
    (r"Analisis Heury,?\s*Elián\s*y\s*Jafet\s*[🧠📊🔠]*", "Analisis Manuel Jimenez"),
    (r"Analisis Heury,?\s*", "Analisis Manuel Jimenez "),
    (r"Elián\s*y\s*Jafet\s*", "Manuel Jimenez "),
    (r"Elián\s*", ""),
    (r"Jafet\s*", ""),
]

# --- CHANNEL NAMES TO REMOVE ---
CHANNEL_NAMES_TO_REMOVE = [
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
]

# --- WORD REPLACEMENTS ---
WORD_REPLACEMENTS = {
    r"LOS VISIONARIOS": "MY TRADING SIGNALS",
    r"Los Visionarios": "My Trading Signals",
    r"VISIONARIOS": "TRADING SIGNALS",
    r"Visionarios": "Trading Signals",
    r"Rendimiento Diario": "Daily Performance",
    r"RENDIMIENTO DIARIO": "DAILY PERFORMANCE",
    r"VENDER": "SELL",
    r"COMPRAR": "BUY",
    r"Vende\b": "SELL",
    r"Compra\b": "BUY",
}

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
    r"xauusd",
    r"eurusd",
    r"gbpusd",
    r"usdjpy",
    r"\bsl\b",
    r"\btp1\b",
    r"\btp2\b",
    r"\btp3\b",
    r"\btp4\b",
    r"asegura el",
    r"asegura tu",
    r"todo en break",
    r"break even",
    r"pagando",
    r"dentro del mejor precio",
    r"seguimos dentro",
    r"pendientes",
    r"cierra",
    r"razón para",
    r"razon para",
    r"patrón",
    r"patron",
    r"engulfing",
    r"base de",
]

# --- SYSTEM VARIABLES ---
SETTINGS = {
    "ai_translate": False,
    "target_language": "en",
    "paused": False,
    "custom_replacements": {},
    "blocked_words": [],
}

print("Starting dual-engine automation pipeline...")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient(StringSession(), API_ID, API_HASH)


def is_authorized(sender_id):
    """Check if user is owner or admin"""
    return sender_id in [OWNER_ID, ADMIN_ID]


def is_audio_message(message):
    if not message.media:
        return False
    if hasattr(message.media, 'document'):
        doc = message.media.document
        if hasattr(doc, 'attributes'):
            for attr in doc.attributes:
                attr_type = type(attr).__name__
                if attr_type in ['DocumentAttributeAudio', 'DocumentAttributeVoice']:
                    return True
    return False


def has_links(text):
    if not text:
        return False
    return bool(re.search(r'https?://\S+|t\.me/\S+|www\.\S+', text, re.IGNORECASE))


def is_allowed_message(text):
    if not text:
        return False
    text_lower = text.lower()
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def is_blocked_word(text):
    if not text:
        return False
    text_lower = text.lower()
    for word in SETTINGS["blocked_words"]:
        if word.lower() in text_lower:
            return True
    return False


def clean_message(text):
    if not text:
        return text

    # Replace admin names
    for pattern, replacement in NAMES_TO_REPLACE:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Remove channel names
    for pattern in CHANNEL_NAMES_TO_REMOVE:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove @usernames and links
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'https?://\S+|t\.me/\S+|www\.\S+', '', text)

    # Apply default word replacements
    for pattern, replacement in WORD_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text)

    # Apply custom replacements added via /addword
    for old, new in SETTINGS["custom_replacements"].items():
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)

    # Clean up
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


# -------------------------------------------------------------------
# COMMAND HANDLER
# -------------------------------------------------------------------
@bot_client.on(events.NewMessage(pattern=r'^/'))
async def command_menu(event):
    if not is_authorized(event.sender_id):
        return

    command = event.text.strip().lower()
    full_text = event.text.strip()

    # /start
    if command == "/start":
        await event.respond(
            "👋 **Welcome to Channel Replicator Bot!**\n\n"
            "I automatically copy trading signals from source channels "
            "to your destination channels.\n\n"
            "Type /help to see all available commands."
        )

    # /help
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
            "➡️ `/ai on` - Enable auto translation\n"
            "➡️ `/ai off` - Disable translation\n"
            "➡️ `/language en` - Translate to English\n"
            "➡️ `/language es` - Translate to Spanish\n"
            "➡️ `/language fr` - Translate to French\n\n"
            "**✏️ Word Management:**\n"
            "➡️ `/addword old:new` - Replace a word\n"
            "➡️ `/removeword word` - Stop replacing a word\n"
            "➡️ `/wordlist` - Show custom replacements\n"
            "➡️ `/blockword word` - Block messages with this word\n"
            "➡️ `/unblockword word` - Unblock a word\n"
            "➡️ `/blocklist` - Show all blocked words\n\n"
            "**📡 Channels:**\n"
            "➡️ `/channels` - Show channel routing\n"
        )

    # /status
    elif command == "/status":
        paused = "⏸ PAUSED" if SETTINGS["paused"] else "▶️ RUNNING"
        translate = "✅ ON" if SETTINGS["ai_translate"] else "🛑 OFF"
        await event.respond(
            f"📊 **Current System Status:**\n\n"
            f"• Bot State: `{paused}`\n"
            f"• Translation: `{translate}`\n"
            f"• Language: `{SETTINGS['target_language'].upper()}`\n"
            f"• Custom Replacements: `{len(SETTINGS['custom_replacements'])}`\n"
            f"• Blocked Words: `{len(SETTINGS['blocked_words'])}`\n\n"
            f"📡 **Routing:**\n"
            f"• HardScalping Room → SCALPING JZ GOLD\n"
            f"• Daytrading Room → DAYTRADING JZ GOLD"
        )

    # /pause
    elif command == "/pause":
        SETTINGS["paused"] = True
        await event.respond(
            "⏸ **Bot Paused.**\n"
            "No messages will be copied until you send /resume"
        )

    # /resume
    elif command == "/resume":
        SETTINGS["paused"] = False
        await event.respond(
            "▶️ **Bot Resumed.**\n"
            "Messages are being copied again."
        )

    # /ai on
    elif command == "/ai on":
        SETTINGS["ai_translate"] = True
        await event.respond(
            f"✅ **Translation Enabled.**\n"
            f"Messages will be translated to `{SETTINGS['target_language'].upper()}`"
        )

    # /ai off
    elif command == "/ai off":
        SETTINGS["ai_translate"] = False
        await event.respond("🛑 **Translation Disabled.** Messages keep original language.")

    # /language
    elif command.startswith("/language "):
        lang = command.split("/language ")[1].strip()
        supported = ["en", "es", "fr", "de", "pt", "ar", "zh", "ru", "it"]
        if lang in supported:
            SETTINGS["target_language"] = lang
            await event.respond(
                f"🌐 **Language set to `{lang.upper()}`**\n"
                f"Enable translation with /ai on"
            )
        else:
            await event.respond(
                f"❌ Unsupported language: `{lang}`\n\n"
                f"Supported: `{', '.join(supported)}`"
            )

    # /addword old:new
    elif full_text.lower().startswith("/addword "):
        try:
            parts = full_text[9:].split(":")
            if len(parts) == 2:
                old_word = parts[0].strip()
                new_word = parts[1].strip()
                SETTINGS["custom_replacements"][old_word] = new_word
                await event.respond(
                    f"✅ **Word replacement added:**\n"
                    f"`{old_word}` → `{new_word}`"
                )
            else:
                await event.respond(
                    "❌ Wrong format. Use:\n`/addword oldword:newword`\n\n"
                    "Example: `/addword VENDER:SELL`"
                )
        except Exception:
            await event.respond("❌ Error. Use: `/addword oldword:newword`")

    # /removeword
    elif full_text.lower().startswith("/removeword "):
        word = full_text[12:].strip()
        if word in SETTINGS["custom_replacements"]:
            del SETTINGS["custom_replacements"][word]
            await event.respond(f"✅ **Removed replacement for:** `{word}`")
        else:
            await event.respond(f"❌ `{word}` not found in replacements.")

    # /wordlist
    elif command == "/wordlist":
        if SETTINGS["custom_replacements"]:
            replacements = "\n".join(
                [f"• `{k}` → `{v}`"
                 for k, v in SETTINGS["custom_replacements"].items()]
            )
            await event.respond(f"📝 **Custom Word Replacements:**\n\n{replacements}")
        else:
            await event.respond("📝 No custom replacements added yet.\nUse `/addword old:new` to add one.")

    # /blockword
    elif full_text.lower().startswith("/blockword "):
        word = full_text[11:].strip()
        if word not in SETTINGS["blocked_words"]:
            SETTINGS["blocked_words"].append(word)
            await event.respond(
                f"🚫 **Word blocked:** `{word}`\n"
                f"Messages containing this word will not be copied."
            )
        else:
            await event.respond(f"⚠️ `{word}` is already blocked.")

    # /unblockword
    elif full_text.lower().startswith("/unblockword "):
        word = full_text[13:].strip()
        if word in SETTINGS["blocked_words"]:
            SETTINGS["blocked_words"].remove(word)
            await event.respond(f"✅ **Word unblocked:** `{word}`")
        else:
            await event.respond(f"❌ `{word}` not found in blocked list.")

    # /blocklist
    elif command == "/blocklist":
        if SETTINGS["blocked_words"]:
            words = "\n".join([f"• `{w}`" for w in SETTINGS["blocked_words"]])
            await event.respond(f"🚫 **Blocked Words:**\n\n{words}")
        else:
            await event.respond("✅ No words blocked.\nUse `/blockword word` to block one.")

    # /channels
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

    for msg in event.messages:
        if is_audio_message(msg):
            return

    caption = None
    for msg in event.messages:
        if msg.message and is_allowed_message(msg.message):
            caption = clean_message(msg.message)
            break

    media_files = [msg.media for msg in event.messages if msg.media]
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

    raw_text = event.message.message
    has_media = event.message.media is not None

    if not raw_text and not has_media:
        return

    if raw_text:
        if not is_allowed_message(raw_text):
            print("⏭️ Skipped: not allowed message type")
            return
        if has_links(raw_text):
            print("⏭️ Skipped: contains links")
            return
        if is_blocked_word(raw_text):
            print("⏭️ Skipped: contains blocked word")
            return

    final_text = None
    if raw_text:
        final_text = clean_message(raw_text)
        if SETTINGS["ai_translate"] and final_text:
            try:
                translated = GoogleTranslator(
                    source='auto',
                    target=SETTINGS["target_language"]
                ).translate(final_text)
                if translated:
                    final_text = translated
            except Exception as e:
                print(f"Translation error: {e}")

    try:
        await user_client.send_message(
            destination_id,
            final_text,
            file=event.message.media
        )
        print(f"✅ Mirrored: {source_id} → {destination_id}")
    except Exception as delivery_error:
        print(f"❌ Delivery failed: {delivery_error}")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
async def main():
    await user_client.connect()
    if not await user_client.is_user_authorized():
        print("❌ ERROR: Session string is invalid or expired!")
        return
    print("✅ Userbot (scraper) is live.")

    await bot_client.start(bot_token=BOT_TOKEN)
    print("✅ Bot control panel is live.")

    print("🚀 Both engines running!")
    print("📡 Golden\"HardScalping\"Room → SCALPING JZ GOLD")
    print("📡 Golden\"Daytrading\"Room → DAYTRADING JZ GOLD")

    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

asyncio.run(main())
