import os
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from googletrans import Translator

# --- ENVIRONMENT CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

SOURCE_CHANNEL = int(os.environ.get("SOURCE_CHANNEL_ID"))
DESTINATION_CHANNEL = int(os.environ.get("DESTINATION_CHANNEL_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))

# --- SYSTEM VARIABLES ---
SETTINGS = {
    "ai_translate": True,
    "target_language": "en"
}

translator = Translator()

# ⚠️ FIX: We separate the Userbot Client and the Admin Bot Client completely
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient('bot_control_session', API_ID, API_HASH)

print("Starting dual-engine automation pipeline...")

# -------------------------------------------------------------------
# FEATURE 1: CONTROL INTERFACE (Handled strictly by the Bot account)
# -------------------------------------------------------------------
@bot_client.on(events.NewMessage(pattern=r'^/', incoming=True))
async def command_menu(event):
    if event.sender_id != OWNER_ID:
        return

    command = event.text.lower()

    if command == "/start":
        await event.respond(
            "⚙️ **Channel Replicator Control Panel**\n\n"
            "Commands:\n"
            "➡️ `/ai on` - Enable automatic translation\n"
            "➡️ `/ai off` - Disable translation (repost original text)\n"
            "➡️ `/status` - Check current bot operations"
        )

    elif command == "/ai on":
        SETTINGS["ai_translate"] = True
        await event.respond("✅ **AI Translation Enabled.** Incoming messages will be translated automatically.")

    elif command == "/ai off":
        SETTINGS["ai_translate"] = False
        await event.respond("🛑 **AI Translation Disabled.** Messages will be mirrored in their raw format.")

    elif command == "/status":
        status_text = (
            "📊 **Current System Status:**\n"
            f"• Translation Active: `{SETTINGS['ai_translate']}`\n"
            f"• Monitoring Channel ID: `{SOURCE_CHANNEL}`\n"
            f"• Broadcasting To ID: `{DESTINATION_CHANNEL}`"
        )
        await event.respond(status_text)

# -------------------------------------------------------------------
# FEATURE 2: SCRAPING ENGINE (Handled strictly by the User session)
# -------------------------------------------------------------------
@user_client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def replication_engine(event):
    raw_text = event.message.message
    final_text = raw_text

    if raw_text:
        if SETTINGS["ai_translate"]:
            try:
                detection = translator.detect(raw_text)
                if detection.lang != SETTINGS["target_language"]:
                    translation = translator.translate(raw_text, dest=SETTINGS["target_language"])
                    final_text = translation.text
            except Exception as e:
                print(f"Translation module error: {e}")
                final_text = raw_text

        # Text filters
        final_text = re.sub(r"Analisis Heury", "MyForexSignals", final_text, flags=re.IGNORECASE)
        final_text = re.sub(r"VENDER", "SELL", final_text, flags=re.IGNORECASE)
        final_text = re.sub(r"COMPRAR", "BUY", final_text, flags=re.IGNORECASE)

    try:
        # Userbot sends the payload directly to the destination channel
        await user_client.send_message(
            DESTINATION_CHANNEL,
            final_text,
            file=event.message.media
        )
        print("Successfully mirrored message event.")
    except Exception as delivery_error:
        print(f"Delivery failed: {delivery_error}")

# -------------------------------------------------------------------
# execution engine block
# -------------------------------------------------------------------
async def start_services():
    # Start both clients asynchronously
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    print("Both Scraper and Bot control panels are live!")

# Run everything on the event loop
import asyncio
loop = asyncio.get_event_loop()
loop.run_until_complete(start_services())

# Keep running until both are disconnected
user_client.run_until_disconnected()
