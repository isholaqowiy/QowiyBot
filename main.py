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
    -1003745031724: -1003820544434,   # Scalping
    -1003189185116: -1003912710963,   # Daytrading
}

# --- NAMES/WATERMARKS TO REMOVE FROM COPIED MESSAGES ---
NAMES_TO_REMOVE = [
    r"Analisis Heury,?\s*",
    r"Elián\s*y\s*Jafet\s*",
    r"Elián\s*",
    r"Jafet\s*",
    r"SCALPING JZ\s*🦅?\s*GOLD\s*🏆?\s*",
    r"SCALPING JZ\s*",
    r"Señal lista\s*",
    r"BlockSavvyMxQ\s*",
    r"MyForexSignals\s*",
    r"Golden\"HardScalping\"Room\s*",
    r"@\w+",  # Remove any @username mentions
]

# --- MESSAGES TO BLOCK COMPLETELY (never copy these) ---
BLOCKED_PHRASES = [
    r"vende oro ahora",
    r"compra oro ahora",
    r"reporte del día",
    r"vamos con el reporte",
    r"familia",
    r"no te quedes fuera",
    r"presume ese profit",
    r"envía tu reporte",
    r"chatderesultados",
    r"días de inactividad",
    r"te elimina",
    r"recuerden que",
    r"para los nuevo",
    r"mensaje fijado",
    r"sigue así",
    r"corrida de oro",
]

# --- SYSTEM VARIABLES ---
SETTINGS = {
    "ai_translate": False,
    "target_language": "en"
}

print("Starting dual-engine automation pipeline...")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient(StringSession(), API_ID, API_HASH)


def is_blocked_message(text):
    """Check if message should be completely blocked"""
    if not text:
        return False
    text_lower = text.lower()
    for phrase in BLOCKED_PHRASES:
        if re.search(phrase, text_lower, re.IGNORECASE):
            print(f"🚫 Blocked message containing: {phrase}")
            return True
    return False


def is_trading_signal(text):
    """Check if message is a valid trading signal to copy"""
    if not text:
        return False
    text_upper = text.upper()
    # Must contain trading keywords
    signal_keywords = [
        "VENDER", "COMPRAR", "SELL", "BUY",
        "TP1", "TP2", "SL", "ENTRAR",
        "XAUUSD", "EURUSD", "GBPUSD",
        "RAZÓN PARA", "RAZON PARA",
        "TP1 ASEGURA", "PAGANDO",
        "PATRÓN", "PATRON", "BASE DE",
        "ENGULFING", "PIPS",
    ]
    for keyword in signal_keywords:
        if keyword in text_upper:
            return True
    return False


def clean_message(text):
    """Remove all source channel names and watermarks"""
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
    source_id = event.chat_id
    destination_id = CHANNEL_MAP.get(source_id)

    if not destination_id:
        return

    raw_text = event.message.message
    has_media = event.message.media is not None

    # --- FILTERING LOGIC ---

    # Rule 1: Block messages with forbidden content
    if raw_text and is_blocked_message(raw_text):
        return

    # Rule 2: Only copy if it's a trading signal OR has media with signal text
    if not has_media and raw_text and not is_trading_signal(raw_text):
        print(f"⏭️ Skipped non-signal message")
        return

    # Rule 3: Skip media-only messages with no text
    # (avoid copying random images not related to signals)
    if has_media and not raw_text:
        print(f"⏭️ Skipped media with no text")
        return

    # --- PROCESS AND SEND ---
    final_text = raw_text

    if raw_text:
        # Step 1: Clean names and watermarks
        final_text = clean_message(raw_text)

        # Step 2: Translate only if enabled
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
        print(f"✅ Mirrored signal from {source_id} → {destination_id}")
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
