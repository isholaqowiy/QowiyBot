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

SOURCE_CHANNEL = int(os.environ.get("SOURCE_CHANNEL_ID"))
DESTINATION_CHANNEL = int(os.environ.get("DESTINATION_CHANNEL_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))

# --- ADMIN/SOURCE NAMES TO REMOVE ---
# Add any names you want completely removed from messages
NAMES_TO_REMOVE = [
    r"Analisis Heury",
    r"Elián",
    r"Jafet",
    r"MyForexSignals",
    r"SCALPING JZ",
    r"Señal lista",
    r"BlockSavvyMxQ",
]

# --- SYSTEM VARIABLES ---
SETTINGS = {
    "ai_translate": True,
    "target_language": "en"
}

print("Starting dual-engine automation pipeline...")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient(StringSession(), API_ID, API_HASH)

def clean_message(text):
    """Remove all admin/source channel names from message"""
    if not text:
        return text
    
    for name in NAMES_TO_REMOVE:
        text = re.sub(name, "", text, flags=re.IGNORECASE)
    
    # Clean up extra blank lines left after name removal
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
            "➡️ `/ai off` - Disable translation\n"
            "➡️ `/status` - Check current bot operations"
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
            f"• Translation Active: `{SETTINGS['ai_translate']}`\n"
            f"• Monitoring Channel ID: `{SOURCE_CHANNEL}`\n"
            f"• Broadcasting To ID: `{DESTINATION_CHANNEL}`"
        )

# -------------------------------------------------------------------
# FEATURE 2: SCRAPING ENGINE (User session)
# -------------------------------------------------------------------
@user_client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def replication_engine(event):
    raw_text = event.message.message
    final_text = raw_text

    if raw_text:
        # Step 1: Remove all admin/source names first
        final_text = clean_message(raw_text)

        # Step 2: Translate if enabled
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

        # Step 3: Fix common trading terms after translation
        final_text = re.sub(r"\bVENDER\b", "SELL", final_text, flags=re.IGNORECASE)
        final_text = re.sub(r"\bCOMPRAR\b", "BUY", final_text, flags=re.IGNORECASE)
        final_text = re.sub(r"\bVende\b", "SELL", final_text, flags=re.IGNORECASE)
        final_text = re.sub(r"\bCompra\b", "BUY", final_text, flags=re.IGNORECASE)

    try:
        await user_client.send_message(
            DESTINATION_CHANNEL,
            final_text,
            file=event.message.media
        )
        print("✅ Successfully mirrored message.")
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

    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

asyncio.run(main())
