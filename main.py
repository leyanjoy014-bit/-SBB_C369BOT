import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

# Import from handlers
from handlers import (
    start_command, help_command, new_topic_start, 
    topic_title, topic_description, topic_category, 
    topic_deadline, my_topics, delete_topic,
    button_callback, cancel_conversation
)
from utils import load_topics

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
TITLE, DESCRIPTION, CATEGORY, DEADLINE = range(4)

def main():
    """Start the bot."""
    # Get bot token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return

    # Create the Updater
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    # Load existing topics
    load_topics()

    # Conversation handler for creating a new topic
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new', new_topic_start)],
        states={
            TITLE: [MessageHandler(Filters.text & ~Filters.command, topic_title)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, topic_description)],
            CATEGORY: [CallbackQueryHandler(topic_category)],
            DEADLINE: [MessageHandler(Filters.text & ~Filters.command, topic_deadline)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
    )

    # Add handlers
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('help', help_command))
    dp.add_handler(CommandHandler('my', my_topics))
    dp.add_handler(CommandHandler('delete', delete_topic))
    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button_callback))

    # Start the Bot
    logger.info("Bot is starting...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
