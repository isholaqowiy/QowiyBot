import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    DocumentAttributeVideo,
    DocumentAttributeAudio,
    DocumentAttributeVoice,
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
    -1003745031724: -1003820544434,
    -1003189185116: -1003912710963,
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
]

# --- WORD REPLACEMENTS ---
WORD_REPLACEMENTS = {
    r"VENDER": "SELL",
    r"COMPRAR": "BUY",
    r"Vende\b": "SELL",
    r"Compra\b": "BUY",
}

# --- IMAGES TO BLOCK (text found in caption) ---
BLOCKED_IMAGE_PHRASES = [
    r"visionarios",
    r"rendimiento diario",
    r"rendimiento del canal",
    r"beneficio neto del día",
    r"tasa de ganancia",
    r"los visionarios",
    r"reporte",
    r"resultado",
    r"canal vip",
    r"señales de day trading",
]

# --- VALID TEXT MESSAGES TO COPY ---
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
    r"stop loss",
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
    r"cierra",
    r"razón para",
    r"razon para",
    r"patrón",
    r"patron",
    r"engulfing",
    r"base de",
    r"super entrada",
    r"hit tp",
    r"corriendo",
    r"alcanzado",
    r"invalidada",
    r"retroceso",
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
    return sender_id in [OWNER_ID, ADMIN_ID]


def is_audio_message(message):
    """Block voice notes and audio files"""
    if not message.media:
        return False
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if hasattr(doc, 'attributes'):
            for attr in doc.attributes:
                if isinstance(attr, (DocumentAttributeAudio, DocumentAttributeVoice)):
                    return True
    return False


def is_video_message(message):
    """Block videos"""
    if not message.media:
        return False
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if hasattr(doc, 'attributes'):
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeVideo):
                    return True
    return False


def is_photo_message(message):
    """Check if message is a photo"""
    return isinstance(message.media, MessageMediaPhoto)


def has_links(text):
    if not text:
        return False
    return bool(re.search(
        r'https?://\S+|t\.me/\S+|www\.\S+',
        text, re.IGNORECASE
    ))


def is_blocked_image(text):
    """Block images with certain captions"""
    if not text:
        return False
    for phrase in BLOCKED_IMAGE_PHRASES:
        if re.search(phrase, text, re.IGNORECASE):
            return True
    return False


def is_allowed_message(text):
    if not text:
        return False
    text_lower = text.lower()
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def is_blocked_word_found(text):
    if not text:
        return False
    for word in SETTINGS["blocked_words"]:
        if word.lower() in text.lower():
            return True
    return False


def clean_message(text):
    if not text:
        return text

    # Replace person names
    for pattern, replacement in NAMES_TO_REPLACE:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Remove channel/brand names
    for pattern in NAMES_TO_REMOVE:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove @usernames and links
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'https?://\S+|t\.me/\S+|www\.\S+', '', text)

    # Apply default replacements
    for pattern, replacement in WORD_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text)

    # Apply custom replacements
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

    if command == "/start":
        await event.respond(
            "👋 **Welcome to Channel Replicator Bot!**\n\n"
            "I automatically copy trading signals from source "
            "channels to your destination channels.\n\n"
            "Type /help to see all available commands."
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
            "➡️ `/language en` - Translate to English\n"
            "➡️ `/language es` - Translate to Spanish\n"
            "➡️ `/language fr` - Translate to French\n\n"
            "**✏️ Word Management:**\n"
            "➡️ `/addword old:new` - Replace a word\n"
            "➡️ `/removeword word` - Remove replacement\n"
            "➡️ `/wordlist` - Show custom replacements\n"
            "➡️ `/blockword word` - Block messages with word\n"
            "➡️ `/unblockword word` - Unblock a word\n"
            "➡️ `/blocklist` - Show blocked words\n\n"
            "**📡 Channels:**\n"
            "➡️ `/channels` - Show channel routing\n"
        )

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

    elif command == "/pause":
        SETTINGS["paused"] = True
        await event.respond(
            "⏸ **Bot Paused.**\n"
            "No messages will be copied until you send /resume"
        )

    elif command == "/resume":
        SETTINGS["paused"] = False
        await event.respond(
            "▶️ **Bot Resumed.**\n"
            "Messages are being copied again."
        )

    elif command == "/ai on":
        SETTINGS["ai_translate"] = True
        await event.respond(
            f"✅ **Translation Enabled.**\n"
            f"Translating to `{SETTINGS['target_language'].upper()}`"
        )

    elif command == "/ai off":
        SETTINGS["ai_translate"] = False
        await event.respond(
            "🛑 **Translation Disabled.**\n"
            "Messages keep original language."
        )

    elif command.startswith("/language "):
        lang = command.split("/language ")[1].strip()
        supported = ["en", "es", "fr", "de", "pt", "ar", "zh", "ru", "it"]
        if lang in supported:
            SETTINGS["target_language"] = lang
            await event.respond(
                f"🌐 **Language set to `{lang.upper()}`**\n"
                f"Enable with /ai on"
            )
        else:
            await event.respond(
                f"❌ Unsupported language: `{lang}`\n"
                f"Supported: `{', '.join(supported)}`"
            )

    elif full_text.lower().startswith("/addword "):
        try:
            parts = full_text[9:].split(":")
            if len(parts) == 2:
                old_word = parts[0].strip()
                new_word = parts[1].strip()
                SETTINGS["custom_replacements"][old_word] = new_word
                await event.respond(
                    f"✅ **Replacement added:**\n`{old_word}` → `{new_word}`"
                )
            else:
                await event.respond(
                    "❌ Wrong format.\nUse: `/addword oldword:newword`"
                )
        except Exception:
            await event.respond("❌ Error. Use: `/addword oldword:newword`")

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
                 for k, v in SETTINGS["custom_replacements"].items()]
            )
            await event.respond(
                f"📝 **Custom Replacements:**\n\n{replacements}"
            )
        else:
            await event.respond(
                "📝 No custom replacements yet.\n"
                "Use `/addword old:new`"
            )

    elif full_text.lower().startswith("/blockword "):
        word = full_text[11:].strip()
        if word not in SETTINGS["blocked_words"]:
            SETTINGS["blocked_words"].append(word)
            await event.respond(f"🚫 **Blocked:** `{word}`")
        else:
            await event.respond(f"⚠️ Already blocked: `{word}`")

    elif full_text.lower().startswith("/unblockword "):
        word = full_text[13:].strip()
        if word in SETTINGS["blocked_words"]:
            SETTINGS["blocked_words"].remove(word)
            await event.respond(f"✅ **Unblocked:** `{word}`")
        else:
            await event.respond(f"❌ `{word}` not in blocked list.")

    elif command == "/blocklist":
        if SETTINGS["blocked_words"]:
            words = "\n".join([f"• `{w}`" for w in SETTINGS["blocked_words"]])
            await event.respond(f"🚫 **Blocked Words:**\n\n{words}")
        else:
            await event.respond(
                "✅ No words blocked.\n"
                "Use `/blockword word`"
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

    # Skip if any audio or video in album
    for msg in event.messages:
        if is_audio_message(msg) or is_video_message(msg):
            print("⏭️ Skipped album: audio/video")
            return

    # Get caption
    caption = None
    for msg in event.messages:
        if msg.message:
            # Block VISIONARIOS images
            if is_blocked_image(msg.message):
                print("⏭️ Skipped album: blocked image content")
                return
            caption = clean_message(msg.message)
            break

    # Only copy photos — no videos
    media_files = []
    for msg in event.messages:
        if is_photo_message(msg):
            media_files.append(msg.media)

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

    # Skip album messages
    if event.message.grouped_id:
        return

    # Skip audio
    if is_audio_message(event.message):
        print("⏭️ Skipped: audio")
        return

    # Skip video
    if is_video_message(event.message):
        print("⏭️ Skipped: video")
        return

    raw_text = event.message.message
    has_media = event.message.media is not None
    is_photo = is_photo_message(event.message)

    # Skip empty
    if not raw_text and not has_media:
        return

    # For photos — check caption
    if is_photo:
        if raw_text and is_blocked_image(raw_text):
            print("⏭️ Skipped: blocked image")
            return
        # Only copy photos that have valid signal text
        # or no caption at all (pure chart)
        if raw_text and not is_allowed_message(raw_text):
            print("⏭️ Skipped: photo with non-signal caption")
            return

    # For text only messages
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

    # Process text
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

    # Send
    try:
        await user_client.send_message(
            destination_id,
            final_text,
            file=event.message.media if is_photo else None
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
