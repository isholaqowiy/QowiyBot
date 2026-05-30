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

# --- CHANNEL ROUTING ---
CHANNEL_MAP = {
    -1003745031724: -1003820544434,
    -1003189185116: -1003912710963,
}

# --- NAMES/WATERMARKS TO REMOVE ---
NAMES_TO_REMOVE = [
    r"Golden\s*\"?HardScalping\"?\s*Room\s*",
    r"Golden\s*\"?Daytrading\"?\s*Room\s*",
    r"Analisis Heury,?\s*",
    r"Elián\s*y\s*Jafet\s*",
    r"Elián\s*",
    r"Jafet\s*",
    r"SCALPING JZ\s*💸?\s*GOLD\s*🌿?\s*",
    r"DAYTRADING JZ\s*💰?\s*GOLD\s*🌿?\s*",
    r"SCALPING JZ\s*🦅?\s*GOLD\s*🏆?\s*",
    r"SCALPING JZ\s*",
    r"DAYTRADING JZ\s*",
    r"Señal lista\s*",
    r"BlockSavvyMxQ\s*",
    r"MyForexSignals\s*",
    r"HARDSCALPING\s*",
    r"@\w+",
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

# --- MESSAGES TO BLOCK ---
BLOCKED_PHRASES = [
    r"los visionarios",
    r"visionarios",
    r"rendimiento diario",
]

# --- SYSTEM VARIABLES ---
SETTINGS = {
    "ai_translate": False,
    "target_language": "en"
}

# --- ALBUM/GROUP TRACKING ---
# Stores grouped media albums temporarily
album_buffer = {}
album_timers = {}

print("Starting dual-engine automation pipeline...")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient(StringSession(), API_ID, API_HASH)


def is_audio_message(message):
    """Detect voice notes and audio files"""
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


def is_blocked_message(text):
    """Block messages mentioning Visionarios"""
    if not text:
        return False
    for phrase in BLOCKED_PHRASES:
        if re.search(phrase, text, re.IGNORECASE):
            print(f"🚫 Blocked: matched '{phrase}'")
            return True
    return False


def clean_message(text):
    """Remove source names and replace watermarks"""
    if not text:
        return text
    for pattern in NAMES_TO_REMOVE:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    for pattern, replacement in WORD_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


async def send_album(destination_id, messages):
    """Send a group of messages as an album"""
    try:
        # Collect all media files
        media_files = []
        caption = None

        for msg in messages:
            if msg.media:
                media_files.append(msg.media)
            if msg.message and not caption:
                caption = clean_message(msg.message)

        if media_files:
            await user_client.send_file(
                destination_id,
                media_files,
                caption=caption
            )
            print(f"✅ Sent album of {len(media_files)} files → {destination_id}")
    except Exception as e:
        print(f"❌ Album send failed: {e}")
        # Fallback: send individually
        for msg in messages:
            try:
                raw_text = msg.message
                final_text = clean_message(raw_text) if raw_text else None
                await user_client.send_message(
                    destination_id,
                    final_text,
                    file=msg.media
                )
            except Exception as e2:
                print(f"❌ Individual send failed: {e2}")


# -------------------------------------------------------------------
# FEATURE 1: CONTROL INTERFACE
# -------------------------------------------------------------------
@bot_client.on(events.NewMessage(pattern=r'^/'))
async def command_menu(event):
    if event.sender_id != OWNER_ID:
        return

    command = event.text.strip().lower()

    if command == "/start":
        await event.respond(
            "⚙️ **Channel Replicator Control Panel**\n\n"
            "Commands:\n"
            "➡️ `/ai on` - Enable translation\n"
            "➡️ `/ai off` - Disable translation (default)\n"
            "➡️ `/status` - Check current bot status"
        )
    elif command == "/ai on":
        SETTINGS["ai_translate"] = True
        await event.respond("✅ **AI Translation Enabled.**")

    elif command == "/ai off":
        SETTINGS["ai_translate"] = False
        await event.respond("🛑 **AI Translation Disabled.**")

    elif command == "/status":
        await event.respond(
            "📊 **Current System Status:**\n"
            f"• Translation Active: `{SETTINGS['ai_translate']}`\n\n"
            "📡 **Channel Routing:**\n"
            "• Golden\"HardScalping\"Room → SCALPING JZ GOLD\n"
            "• Golden\"Daytrading\"Room → DAYTRADING JZ GOLD\n\n"
            "⚙️ **Rules:**\n"
            "• Texts: ✅ Copied\n"
            "• Images: ✅ Copied grouped\n"
            "• Audios: ❌ Blocked\n"
            "• Source names: ❌ Removed"
        )


# -------------------------------------------------------------------
# FEATURE 2: SCRAPING ENGINE
# -------------------------------------------------------------------
@user_client.on(events.Album(chats=list(CHANNEL_MAP.keys())))
async def album_handler(event):
    """Handle grouped media albums"""
    source_id = event.chat_id
    destination_id = CHANNEL_MAP.get(source_id)

    if not destination_id:
        return

    # Check if any message in album is audio
    for msg in event.messages:
        if is_audio_message(msg):
            print("⏭️ Skipped album: contains audio")
            return

    # Check blocked phrases in any message text
    for msg in event.messages:
        if msg.message and is_blocked_message(msg.message):
            print("⏭️ Skipped album: blocked content")
            return

    # Send as grouped album
    await send_album(destination_id, event.messages)


@user_client.on(events.NewMessage(chats=list(CHANNEL_MAP.keys())))
async def replication_engine(event):
    """Handle individual messages"""
    source_id = event.chat_id
    destination_id = CHANNEL_MAP.get(source_id)

    if not destination_id:
        return

    # Skip if part of an album (handled by album_handler)
    if event.message.grouped_id:
        return

    raw_text = event.message.message
    has_media = event.message.media is not None

    # Rule 1: Skip audio messages
    if is_audio_message(event.message):
        print("⏭️ Skipped: audio/voice message")
        return

    # Rule 2: Skip empty messages
    if not raw_text and not has_media:
        print("⏭️ Skipped: empty message")
        return

    # Rule 3: Block Visionarios messages
    if raw_text and is_blocked_message(raw_text):
        return

    # Process message
    final_text = raw_text
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

    # Send to destination
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
