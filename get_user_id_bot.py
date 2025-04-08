from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '7830363495:AAFhO3KMRDTkWkh8KXCA3CWLSYOpKOX1jM4'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('напиши чёнить')

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text(f'Ваш ID: {user_id} , перешли это сообщение илюхе')

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_id))

    application.run_polling()

if __name__ == '__main__':
    main()