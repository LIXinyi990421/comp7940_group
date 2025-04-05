from telegram import Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackContext)
import configparser
import logging
from ChatGPT_HKBU import HKBU_ChatGPT
from pymongo import MongoClient
from typing import Optional
from bson import ObjectId

# Global variables
global mongo_client, db, config, chatgpt


def main():
    # Load configuration
    global config, mongo_client, db, chatgpt
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Initialize logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Initialize MongoDB connection
    try:
        mongo_client = MongoClient(
            config['MONGODB']['CONN_STRING'],
            serverSelectionTimeoutMS=5000
        )
        mongo_client.server_info()  # Test connection
        db = mongo_client[config['MONGODB']['DB_NAME']]
        logging.info(f"Successfully connected to MongoDB. Shard key field: {config['MONGODB']['SHARD_KEY_FIELD']}")
    except Exception as e:
        logging.error(f"MongoDB connection failed: {e}")
        raise

    # Initialize Telegram Bot
    updater = Updater(token=config['TELEGRAM']['ACCESS_TOKEN'], use_context=True)
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("hello", hello))

    # Initialize ChatGPT
    chatgpt = HKBU_ChatGPT()
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), equip_chatgpt)
    dispatcher.add_handler(chatgpt_handler)

    # Start the Bot
    updater.start_polling()
    logging.info("Bot is running...")
    updater.idle()


def help_command(update: Update, context: CallbackContext) -> None:
    try:
        update.message.reply_text(
            '🌟 Available commands:\n'
            '/add <keyword> - Count statistics\n'
            '/hello <name> - Greet someone\n'
            '/help - Show help\n\n'
            '💡 Features:\n'
            '1. Send "recommend activities" to get interest-based suggestions\n'
            '2. Send "find partners" to find partners with shared interests'
        )
    except Exception as e:
        logging.error(f"Help command error:{e}")


def add(update: Update, context: CallbackContext) -> None:
    global config, mongo_client, db, chatgpt
    try:
        if not context.args:
            raise ValueError("Missing keyword")

        keyword = ' '.join(context.args)
        shard_key = config['MONGODB']['SHARD_KEY_FIELD']

        # Build query with shard key
        query = {"_id": keyword}
        if shard_key != "_id":
            query[shard_key] = keyword  # Add shard key field

        result = db.counters.update_one(
            query,
            {"$inc": {"count": 1}},
            upsert=True
        )

        # Get latest count
        doc = db.counters.find_one({"_id": keyword})
        new_count = doc["count"] if doc else 1

        update.message.reply_text(f'✅ [{keyword}] Count updated: {new_count}')

    except Exception as e:
        logging.error(f"Add command error: {e}")
        update.message.reply_text('❌ Usage: /add <keyword>')


def hello(update: Update, context: CallbackContext) -> None:
    global config, mongo_client, db, chatgpt
    try:
        name = ' '.join(context.args) or 'friend'
        update.message.reply_text(f'👋 Hello, {name}!')
    except:
        update.message.reply_text('❌ Usage: /hello <name>')


  


if __name__ == '__main__':
    main()