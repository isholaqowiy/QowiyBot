import os
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from googletrans import Translator

# --- ENVIRONMENT CONFIGURATION (Render variables) ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

SOURCE_CHANNEL = int(os.environ.get("SOURCE_CHANNEL_ID"))
DESTINATION_CHANNEL = int(os.environ.get("DESTINATION_CHANNEL_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))  # Your client's Telegram User ID

# --- SYSTEM VARIABLES (Stored in memory) ---
# Default settings: Translation and text replacement are enabled by default
SETTINGS = {
    "ai_translate": True,
    "target_language": "en"  # Default translation target (English)
}

# Initialize Translator
translator = Translator()

# Initialize the Telethon Client with both User Session and Bot Token
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

print("Starting Channel Mirroring Engine...")

# -------------------------------------------------------------------
# FEATURE 1: CONTROL INTERFACE (Bot Commands)
# -------------------------------------------------------------------
@client.on(events.NewMessage(pattern=r'^/', incoming=True))
async def command_menu(event):
    # Only allow the designated owner to change configurations
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
        await event.respond("✅ **AI Translation Enabled.** All upcoming incoming messages will be translated automatically.")

    elif command == "/ai off":
        SETTINGS["ai_translate"] = False
        await event.respond("🛑 **AI Translation Disabled.** Messages will now be mirrored in their raw original format.")

    elif command == "/status":
        status_text = (
            "📊 **Current System Status:**\n"
            f"• Translation Active: `{SETTINGS['ai_translate']}`\n"
            f"• Target Language: `{SETTINGS['target_language'].upper()}`\n"
            f"• Monitoring Channel ID: `{SOURCE_CHANNEL}`\n"
            f"• Broadcasting To ID: `{DESTINATION_CHANNEL}`"
        )
        await event.respond(status_text)

# -------------------------------------------------------------------
# FEATURE 2: AUTOMATED DUPLICATION & TRANSLATION ENGINE
# -------------------------------------------------------------------
@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def replication_engine(event):
    raw_text = event.message.message
    final_text = raw_text

    # Only process text customization if a message contains string contents
    if raw_text:
        # Step A: Perform Translation if turned on
        if SETTINGS["ai_translate"]:
            try:
                detection = translator.detect(raw_text)
                # Only translate if the source text isn't already in our target language
                if detection.lang != SETTINGS["target_language"]:
                    translation = translator.translate(raw_text, dest=SETTINGS["target_language"])
                    final_text = translation.text
            except Exception as e:
                print(f"Translation module error: {e}. Defaulting to raw text copy.")
                final_text = raw_text

        # Step B: Clean/Personalize Text (e.g., removing original channel names or formatting)
        # Example: Replacing Spanish trading markers or channel signatures dynamically
        final_text = re.sub(r"Analisis Heury", "MyForexSignals", final_text, flags=re.IGNORECASE)
        final_text = re.sub(r"VENDER", "SELL", final_text, flags=re.IGNORECASE)
        final_text = re.sub(r"COMPRAR", "BUY", final_text, flags=re.IGNORECASE)

    # Step C: Mirror the complete post payload directly to the client's destination channel
    try:
        await client.send_message(
            DESTINATION_CHANNEL,
            final_text,
            file=event.message.media  # Preserves all charts, screenshots, graphics, and media
        )
        print("Successfully translated, processed, and mirrored signal event.")
    except Exception as delivery_error:
        print(f"Failed to post to target channel: {delivery_error}")

# Run the system with both the Userbot credentials and Bot control profile token
client.start(bot_token=BOT_TOKEN)
client.run_until_disconnected()
