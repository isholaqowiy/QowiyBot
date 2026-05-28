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
# Golden"HardScalping"Room → SCALPING JZ GOLD
# Golden"Daytrading"Room   → DAYTRADING JZ GOLD
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
    r"Los Visionarios\s*",
    r"Visionarios\s*",
    r"HARDSCALPING\s*",
    r"Rendimiento Diario\s*",
    r"@\w+",
]

# --- MESSAGES TO BLOCK COMPLETELY ---
BLOCKED_PHRASES = [
    r"vende oro ahora",
    r"compra oro ahora",
    r"vamos con el reporte",
    r"reporte del día",
    r"reporte del dia",
    r"rendimiento diario",
    r"los visionarios",
    r"visionarios",
    r"no te quedes fuera",
    r"presume ese profit",
    r"show off that profit",
    r"envía tu reporte",
    r"submit your report",
    r"chatderesultados",
    r"chat de resultados",
    r"días de inactividad",
    r"days of inactivity",
    r"te elimina",
    r"does not eliminate",
    r"recuerden que",
    r"remember that",
    r"para los nuevo",
    r"mensaje fijado",
    r"sigue así",
    r"keep like this",
    r"corrida de oro",
    r"gold run",
    r"faster broker",
    r"broker withdrawal",
    r"sesión sólida",
    r"solid session",
    r"familia",
    r"seguimos",
    r"beneficio neto",
    r"tasa de ganancia",
    r"ganadas",
    r"perdidas",
    r"let's go with the report",
    r"don't be left out",
    r"day family",
    r"señal lista",
    r"\+\d+\s*pips",
]

# --- VALID TRADING SIGNAL KEYWORDS ---
SIGNAL_KEYWORDS = [
    "VENDER", "COMPRAR", "SELL", "BUY",
    "TP1", "TP2", "TP3", "SL",
    "ENTRAR", "ENTRY",
    "XAUUSD", "EURUSD", "GBPUSD", "USDJPY",
    "RAZÓN PARA", "RAZON PARA",
    "PATRÓN", "PATRON",
    "BASE DE", "ENGULFING",
    "TP1 ASEGURA", "TP1 SECURES",
    "PAGANDO",
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
    if not text:
        return False
    text_lower = text.lower()
    for phrase in BLOCKED_PHRASES:
        if re.search(phrase, text_lower, re.IGNORECASE):
            print(f"🚫 Blocked: matched '{phrase}'")
            return True
    return False


def is_valid_signal(text):
    if not text:
        return False
    text_upper = text.upper()
    for keyword in SIGNAL_KEYWORDS:
        if keyword in text_upper:
            return True
    return False


def clean_message(text):
    if not text:
        return text
    for pattern in NAMES_TO_REMOVE:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bVENDER\b", "SELL", text, flags=re.IGNORECASE)
    text = re.sub(r"\bCOMPRAR\b", "BUY", text, flags=re.IGNORECASE)
    text = re.sub(r"\bVende\b", "SELL", text, flags=re.IGNORECASE)
    text = re.sub(r"\bCompra\b", "BUY", text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


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
            "• Golden\"Daytrading\"Room → DAYTRADING JZ GOLD"
        )


# -------------------------------------------------------------------
# FEATURE 2: SCRAPING ENGINE
# -------------------------------------------------------------------
@user_client.on(events.NewMessage(chats=list(CHANNEL_MAP.keys())))
async def replication_engine(event):
    source_id = event.chat_id
    destination_id = CHANNEL_MAP.get(source_id)

    if not destination_id:
        return

    raw_text = event.message.message
    has_media = event.message.media is not None

    # Block forbidden messages
    if raw_text and is_blocked_message(raw_text):
        return

    # Text only — must be valid signal
    if not has_media:
        if not raw_text or not is_valid_signal(raw_text):
            print("⏭️ Skipped: not a valid trading signal")
            return

    # Media — must have valid signal text
    if has_media:
        if not raw_text or not is_valid_signal(raw_text):
            print("⏭️ Skipped: media without valid signal text")
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
