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
# Source 1 (Scalping) → Destination 1
# Source 2 (Daytrading) → Destination 2
CHANNEL_MAP = {
    -1003745031724: -1003820544434,   # Scalping
    -1003189185116: -1003912710963,   # Daytrading
}

# --- NAMES/WATERMARKS TO REMOVE ---
NAMES_TO_REMOVE = [
    r"Analisis Heury",
    r"Elián\s*y\s*Jafet",
    r"Elián",
    r"Jafet",
    r"SCALPING JZ\s*🦅?\s*GOLD\s*🏆?",
    r"SCALPING JZ",
    r"Señal lista",
    r"BlockSavvyMxQ",
    r"MyForexSignals",
    r"@\w+",  # Remove any @username mentions
]

# --- SYSTEM VARIABLES ---
SETTINGS = {
    "ai_translate": False,  # OFF by default — only translate when commanded
    "target_language": "en"
}

print("Starting dual-engine automation pipeline...")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient(StringSession(), API_ID, API_HASH)


def clean_message(text):
    """Remove all source channel names, admin names and watermarks"""
    if not text:
        return text

    for pattern in NAMES_TO_REMOVE:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Fix trading terms
    text = re.sub(r"\bVENDER\b", "SELL", text, flags=re.IGNORECASE)
    text = re.sub(r"\bCOMPRAR\b", "BUY", text, flags=re.IGNORECASE)
    text = re.sub(r"\bVende\b", "SELL", text, flags=re.IGNORECASE)
    text = re.sub(r"\bCompra\b", "BUY", text, flags=re.IGNORECASE)

    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


# -------------------------------------------------------------------
# FEATURE 1: CONTROL INTERFACE (Bot account)
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
            "➡️ `/ai on` - Enable automatic translation\n"
            "➡️ `/ai off` - Disable translation (default)\n"
            "➡️ `/status` - Check current bot status\n\n"
            "📡 **Monitoring:**\n"
            "• Scalping channel → Your scalping channel\n"
            "• Daytrading channel → Your daytrading channel"
        )

    elif command == "/ai on":
        SETTINGS["ai_translate"] = True
        await event.respond("✅ **AI Translation Enabled.** Messages will be translated to English.")

    elif command == "/ai off":
        SETTINGS["ai_translate"] = False
        await event.respond("🛑 **AI Translation Disabled.** Messages will keep their original language.")

    elif command == "/status":
        await event.respond(
            "📊 **Current System Status:**\n"
            f"• Translation Active: `{SETTINGS['ai_translate']}`\n"
            f"• Scalping Source: `-1003745031724`\n"
            f"• Scalping Destination: `-1003820544434`\n"
            f"• Daytrading Source: `-1003189185116`\n"
            f"• Daytrading Destination: `-1003912710963`"
        )


# -------------------------------------------------------------------
# FEATURE 2: SCRAPING ENGINE (User session)
# -------------------------------------------------------------------
@user_client.on(events.NewMessage(chats=list(CHANNEL_MAP.keys())))
async def replication_engine(event):
    # Get the correct destination for this source
    source_id = event.chat_id
    destination_id = CHANNEL_MAP.get(source_id)

    if not destination_id:
        print(f"⚠️ No destination mapped for source: {source_id}")
        return

    raw_text = event.message.message
    final_text = raw_text

    if raw_text:
        # Step 1: Clean names and watermarks
        final_text = clean_message(raw_text)

        # Step 2: Translate only if enabled by command
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
        print(f"✅ Mirrored message from {source_id} → {destination_id}")
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

    print("🚀 Both engines running — monitoring 2 source channels!")

    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

asyncio.run(main())
