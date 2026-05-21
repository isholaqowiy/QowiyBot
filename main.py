import os
import re
import asyncio
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

# Use StringSession for BOTH clients so nothing is written to disk
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient(StringSession(), API_ID, API_HASH)  # Bot uses memory session

print("Starting dual-engine automation pipeline...")

# -------------------------------------------------------------------
# FEATURE 1: CONTROL INTERFACE (Bot account)
# -------------------------------------------------------------------
@bot_client.on(events.NewMessage(pattern=r'^/'))
async def command_menu(event):
    # Only respond to the owner
    if event.sender_id != OWNER_ID:
        return

    command = event.text.strip().lower()

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
# FEATURE 2: SCRAPING ENGINE (User session)
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
        await user_client.send_message(
            DESTINATION_CHANNEL,
            final_text,
            file=event.message.media
        )
        print("✅ Successfully mirrored message event.")
    except Exception as delivery_error:
        print(f"❌ Delivery failed: {delivery_error}")

# -------------------------------------------------------------------
# MAIN ASYNC ENTRY POINT — THE CRITICAL FIX
# -------------------------------------------------------------------
async def main():
    # Start user client (already has session string)
    await user_client.start()
    print("✅ Userbot (scraper) is live.")

    # Start bot client with bot token
    await bot_client.start(bot_token=BOT_TOKEN)
    print("✅ Bot control panel is live.")

    print("🚀 Both engines running. Listening for events...")

    # THIS IS THE KEY FIX:
    # Run BOTH clients concurrently and keep them alive together
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

asyncio.run(main())
