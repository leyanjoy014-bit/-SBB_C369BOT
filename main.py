import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from bot.handlers import (
    start_command, help_command, new_topic_start, 
    topic_title, topic_description, topic_category, 
    topic_deadline, my_topics, delete_topic,
    button_callback, cancel_conversation
)
from bot.utils import load_topics

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

    # Create the Application
    application = Application.builder().token(token).build()

    # Load existing topics
    load_topics()

    # Conversation handler for creating a new topic
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new', new_topic_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, topic_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, topic_description)],
            CATEGORY: [CallbackQueryHandler(topic_category)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, topic_deadline)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
    )

    # Add handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('my', my_topics))
    application.add_handler(CommandHandler('delete', delete_topic))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the Bot
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
