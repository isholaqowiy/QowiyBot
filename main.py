import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
)
from telethon.errors import (
    SessionExpiredError,
    SessionRevokedError,
    AuthKeyUnregisteredError,
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
    -1003745031724: -1003820544434,  # HardScalping → SCALPING JZ GOLD
    -1003189185116: -1003912710963,  # Daytrading → DAYTRADING JZ GOLD
}

# --- NAMES TO REPLACE ---
NAMES_TO_REPLACE = [
    (r"Analisis Heury,?\s*Elián\s*y\s*Jafet\s*[🧠📊🔠]*\s*",
     "Analisis Manuel Jimenez "),
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
    r"\bVENDER\b": "SELL",
    r"\bCOMPRAR\b": "BUY",
    r"\bVende\b": "SELL",
    r"\bCompra\b": "BUY",
}

# --- IMAGES TO BLOCK ---
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
    r"canal vip",
    r"participantes",
    r"subscribe",
    r"suscri",
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

print("Starting Omar Channel Replicator Bot...")

user_client = TelegramClient(
    StringSession(SESSION_STRING), API_ID, API_HASH
)
bot_client = TelegramClient(StringSession(), API_ID, API_HASH)


# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------
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
    if not text:
        return False
    for phrase in BLOCKED_IMAGE_PHRASES:
        if re.search(phrase, text, re.IGNORECASE):
            print(f"🚫 Blocked image: {phrase}")
            return True
    return False


def is_allowed_message(text):
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
            "⚙️ **Channel Replicator Control Panel**\n\n"
            "Commands:\n"
            "➡️ `/help` - All commands\n"
            "➡️ `/status` - Current bot status\n"
            "➡️ `/pause` - Pause copying\n"
            "➡️ `/resume` - Resume copying\n"
            "➡️ `/ai on` - Enable translation\n"
            "➡️ `/ai off` - Disable translation\n"
            "➡️ `/ping` - Check bot is alive"
        )

    elif command == "/help":
        await event.respond(
            "📋 **Available Commands:**\n\n"
            "**🔧 System:**\n"
            "➡️ `/start` - Welcome message\n"
            "➡️ `/help` - Show all commands\n"
            "➡️ `/status` - Current bot status\n"
            "➡️ `/ping` - Check bot is alive\n\n"
            "**⏯ Control:**\n"
            "➡️ `/pause` - Pause all copying\n"
            "➡️ `/resume` - Resume copying\n\n"
            "**🌐 Translation:**\n"
            "➡️ `/ai on` - Enable translation\n"
            "➡️ `/ai off` - Disable translation\n"
            "➡️ `/language en` - English\n"
            "➡️ `/language es` - Spanish\n\n"
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

    elif command == "/ping":
        await event.respond(
            "🏓 **Pong!**\n"
            "✅ Bot is alive and running.\n"
            "📡 Monitoring both source channels."
        )

    elif command == "/status":
        paused = (
            "⏸ PAUSED" if SETTINGS["paused"] else "▶️ RUNNING"
        )
        translate = (
            "✅ ON" if SETTINGS["ai_translate"] else "🛑 OFF"
        )
        await event.respond(
            f"📊 **Current System Status:**\n\n"
            f"• Bot State: `{paused}`\n"
            f"• Translation: `{translate}`\n"
            f"• Language: `{SETTINGS['target_language'].upper()}`\n"
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
        await event.respond(
            f"✅ **Translation ON** → "
            f"`{SETTINGS['target_language'].upper()}`"
        )

    elif command == "/ai off":
        SETTINGS["ai_translate"] = False
        await event.respond("🛑 **Translation OFF.**")

    elif command.startswith("/language "):
        lang = command.split("/language ")[1].strip()
        supported = [
            "en", "es", "fr", "de", "pt",
            "ar", "zh", "ru", "it"
        ]
        if lang in supported:
            SETTINGS["target_language"] = lang
            await event.respond(
                f"🌐 **Language set to `{lang.upper()}`**"
            )
        else:
            await event.respond(
                f"❌ Unsupported: `{lang}`\n"
                f"Try: {', '.join(supported)}"
            )

    elif full_text.lower().startswith("/addword "):
        try:
            parts = full_text[9:].split(":")
            if len(parts) == 2:
                old_word = parts[0].strip()
                new_word = parts[1].strip()
                SETTINGS["custom_replacements"][old_word] = (
                    new_word
                )
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
            if is_blocked_image(raw):
                print("⏭️ Skipped album: blocked image")
                return
            if is_allowed_message(raw):
                has_valid_caption = True
                caption = clean_message(raw)
                break

    if not has_valid_caption:
        print("⏭️ Skipped album: no valid signal caption")
        return

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

    # Strict photo filtering
    if is_photo:
        if not raw_text:
            print("⏭️ Skipped: photo with no caption")
            return
        if is_blocked_image(raw_text):
            print("⏭️ Skipped: blocked image phrase")
            return
        if not is_allowed_message(raw_text):
            print("⏭️ Skipped: photo not a valid signal")
            return

    # Text only filtering
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

    # Process and send
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
# RESILIENT CLIENT RUNNER
# -------------------------------------------------------------------
async def run_client_forever(client, name, start_kwargs=None):
    """Keep client connected indefinitely with auto-reconnect."""
    backoff = 5
    while True:
        try:
            if not client.is_connected():
                await client.connect()

            if start_kwargs is not None:
                await client.start(**start_kwargs)
            else:
                if not await client.is_user_authorized():
                    print(
                        f"❌ {name} session invalid/expired!\n"
                        "Please generate a new session string."
                    )
                    return

            print(f"✅ {name} connected.")
            backoff = 5
            await client.run_until_disconnected()
            print(f"⚠️ {name} disconnected. Reconnecting...")

        except (
            SessionExpiredError,
            SessionRevokedError,
            AuthKeyUnregisteredError,
        ) as e:
            print(f"❌ Fatal session error on {name}: {e}")
            print("Please generate a new session string.")
            return
        except Exception as e:
            print(f"⚠️ {name} error: {e}")
            print(f"🔄 Retrying {name} in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
async def main():
    print("Connecting userbot...")
    await user_client.connect()

    try:
        if not await user_client.is_user_authorized():
            print("❌ Session string invalid or expired!")
            print("Please generate a new session string.")
            return
    except (
        SessionExpiredError,
        SessionRevokedError,
        AuthKeyUnregisteredError,
    ) as e:
        print(f"❌ Session error: {e}")
        return

    print("✅ Userbot connected and authorized.")
    print("📡 Source 1: Golden\"HardScalping\"Room")
    print("📡 Source 2: Golden\"Daytrading\"Room")

    await bot_client.start(bot_token=BOT_TOKEN)
    print("✅ Bot control panel connected.")

    print("\n🚀 Omar Channel Replicator Bot RUNNING!")
    print("📡 HardScalping Room → SCALPING JZ GOLD")
    print("📡 Daytrading Room → DAYTRADING JZ GOLD")
    print("🚫 Visionarios images: BLOCKED\n")

    await asyncio.gather(
        run_client_forever(user_client, "Userbot"),
        run_client_forever(
            bot_client, "Bot",
            start_kwargs={"bot_token": BOT_TOKEN}
        ),
    )


asyncio.run(main())
