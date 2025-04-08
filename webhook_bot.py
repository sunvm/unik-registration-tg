from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import telegram
from mcrcon import MCRcon
import warnings
from telegram.warnings import PTBUserWarning
import json
import os
from datetime import datetime, timedelta
from config import TOKEN, RCON_HOST, RCON_PORT, RCON_PASSWORD, ADMIN_IDS, ADMIN_NAMES

# Подавляем конкретное предупреждение
warnings.filterwarnings('ignore', category=PTBUserWarning)

# Настройки webhook
WEBHOOK_HOST = 'your-domain.com'  # Замените на ваш домен
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'https://{WEBHOOK_HOST}{WEBHOOK_PATH}'

# Настройки веб-сервера
WEBAPP_HOST = 'localhost'
WEBAPP_PORT = 8443

async def main():
    # Создаем приложение
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Добавляем обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            RULES: [CallbackQueryHandler(rules_handler, pattern='^rules:')],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_handler)],
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nickname_handler)],
            OTHER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_info_handler)]
        },
        fallbacks=[],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button))
    
    # Настраиваем webhook
    await application.bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES
    )
    
    # Запускаем веб-сервер
    await application.run_webhook(
        listen=WEBAPP_HOST,
        port=WEBAPP_PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL
    )

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 