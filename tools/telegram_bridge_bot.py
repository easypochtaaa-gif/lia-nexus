#!/usr/bin/env python3
"""telegram_bridge_bot.py

A lightweight Telegram "mirror" bot that acts as a bridge between a user and the real
service bot @Help_Pay_Business_bot.

Workflow:
1. User sends a message (e.g., a phone number) to this bridge bot.
2. The bridge forwards the exact text to @Help_Pay_Business_bot using the Bot API's
   forwardMessage / copyMessage capabilities.
3. It listens for a reply from the real bot that references the forwarded message
   (reply_to_message). When such a reply arrives, the bridge extracts the text and
   sends it back to the original user.

Configuration:
- Place a Telegram Bot token for this bridge bot in the project .env file:
    TELEGRAM_BRIDGE_TOKEN=YOUR_BRIDGE_BOT_TOKEN
- Ensure the bridge bot has been added to the same group/chat as @Help_Pay_Business_bot
  or start a private conversation with both bots (the bridge can only forward
  messages it can access).

Dependencies (install via pip):
    pip install python-telegram-bot==20.*

Run the script:
    python tools/telegram_bridge_bot.py
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load the bridge bot token from .env (project root)
BRIDGE_TOKEN = os.getenv("TELEGRAM_BRIDGE_TOKEN")
if not BRIDGE_TOKEN:
    raise RuntimeError("TELEGRAM_BRIDGE_TOKEN not set in .env")

# The target real bot username (cannot be a token, just the @username)
TARGET_BOT_USERNAME = "Help_Pay_Business_bot"

async def forward_to_real_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming user messages and forward them to the real bot.
    The original message id is stored in the reply markup so we can match the
    response later.
    """
    user_msg = update.effective_message
    if not user_msg or not user_msg.text:
        return
    # Forward (copy) the message to the target bot by sending it to the bot's chat.
    # If the bridge and real bot share a private chat, use that chat id.
    # Otherwise, we assume they are in a group; we use the username as a shortcut.
    try:
        await context.bot.send_message(
            chat_id=f"@{TARGET_BOT_USERNAME}",
            text=user_msg.text,
            reply_markup=user_msg.reply_markup,
        )
        logger.info("Forwarded message from %s to %s", update.effective_user.id, TARGET_BOT_USERNAME)
    except Exception as e:
        logger.error("Failed to forward message: %s", e)

async def relay_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When the real bot replies, send that reply back to the original user.
    The real bot's reply should have reply_to_message referencing the forwarded
    message. We extract the original sender from that reference.
    """
    msg = update.effective_message
    if not msg or not msg.reply_to_message:
        return
    # The original forwarded message contains the user id in its "forward_from" field.
    original_sender = msg.reply_to_message.forward_from
    if not original_sender:
        # In some cases forward_from may be None; fallback to the chat id if it's a private chat.
        original_sender = msg.reply_to_message.chat
    try:
        await context.bot.send_message(
            chat_id=original_sender.id if hasattr(original_sender, "id") else original_sender,
            text=msg.text or "[no text]",
        )
        logger.info("Relayed reply to user %s", original_sender.id if hasattr(original_sender, "id") else original_sender)
    except Exception as e:
        logger.error("Failed to relay reply: %s", e)

def main() -> None:
    app = ApplicationBuilder().token(BRIDGE_TOKEN).build()
    # Handle any text from users (private chat or group mentions)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_real_bot))
    # Handle replies that come from the real bot (we identify by username)
    app.add_handler(MessageHandler(filters.User(username=TARGET_BOT_USERNAME) & filters.REPLY, relay_reply))
    logger.info("Telegram bridge bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
