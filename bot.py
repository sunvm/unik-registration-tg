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

# Состояния для ConversationHandler
RULES, AGE, NICKNAME, OTHER_INFO = range(4)

# Файл для хранения информации о заявках
APPLICATIONS_FILE = 'applications.json'

def load_applications():
    if os.path.exists(APPLICATIONS_FILE):
        with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_applications(applications):
    with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(applications, f, ensure_ascii=False, indent=4)

def can_submit_application(user_id):
    if user_id in ADMIN_IDS:
        return True, None
    
    applications = load_applications()
    user_apps = applications.get(str(user_id), [])
    
    if not user_apps:
        return True, None
    
    last_app = user_apps[-1]
    last_date = datetime.fromisoformat(last_app['date'])
    
    if last_app['status'] == 'approved':
        return False, "Ваша предыдущая заявка была одобрена. Повторная подача заявки невозможна."
    
    if last_app['status'] == 'rejected':
        if datetime.now() - last_date < timedelta(days=7):
            days_left = 7 - (datetime.now() - last_date).days
            return False, f"Ваша предыдущая заявка была отклонена. Вы сможете подать новую заявку через {days_left} дней."
    
    return True, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    can_submit, message = can_submit_application(user_id)
    if not can_submit:
        await update.message.reply_text(message)
        return ConversationHandler.END

    welcome_message = (
        "Добро пожаловать на сервер! Перед началом регистрации прочитай правила:\n\n"
        "Правила сервера Майнкрафт\n\n"
        "Не гриферить (Под приферством подразумевается разрушение любым способом чужих построек без разрешения, "
        "заливание лавой, водой и т.п; убийство игроков без причины; убийство животных и/или мобов на фермах игроков)\n"
        "────┈┈┈┄┄╌╌╌╌┄┄┈┈┈────\n"
        "Не оскорблять игроков\n"
        "────┈┈┈┄┄╌╌╌╌┄┄┈┈┈────\n"
        "Запрещены политические темы (обсуждения, оскорбление символики, демонстрация оскорбительной символики)\n"
        "────┈┈┈┄┄╌╌╌╌┄┄┈┈┈────\n"
        "Запрещены читы (любого формата)\n"
        "────┈┈┈┄┄╌╌╌╌┄┄┈┈┈────\n"
        "Не воровать чужие вещи/животных\n"
        "────┈┈┈┄┄╌╌╌╌┄┄┈┈┈────\n"
        "Не строить огромные фермы и механизмы, которые очень сильно нагружают сервер и снижают tps\n"
        "────┈┈┈┄┄╌╌╌╌┄┄┈┈┈────\n"
        "Если игрок огородил СВОЮ территорию и/или поставил предупреждающую табличку, в которой написано "
        "\"вход запрещён\", \"вход только ... \", то остальные игроки должны выполнять эти условия. "
        "(только если это не нарушает границы других игроков)\n"
        "────┈┈┈┄┄╌╌╌╌┄┄┈┈┈────\n"
        "Администратор имеет право не принять вашу заявку по причине оскорбляющего ника либо неадекватного поведения\n"
        "────┈┈┈┄┄╌╌╌╌┄┄┈┈┈────\n"
        "При отсутствии игрока более чем 3 месяца по неуважительной причине, его постройки будут приватизированы "
        "(снесены/перестроены/достроены и так далее.)\n\n"
        "Вы изучили правила сервера?"
    )

    keyboard = [
        [
            InlineKeyboardButton("Да, согласен", callback_data="rules:yes"),
            InlineKeyboardButton("Нет, не согласен", callback_data="rules:no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return RULES

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    await update.message.reply_text('Ваш игровой ник')
    return NICKNAME

async def nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['nickname'] = update.message.text
    user_data = context.user_data
    user = update.effective_user
    # Создаем ссылку на профиль пользователя
    user_link = f'<a href="tg://user?id={user.id}">{user_data["nickname"]}</a>'
    
    survey_result = (
        f"Изучил правила: {user_data['rules_acknowledged']}\n"
        f"Возраст: {user_data['age']}\n"
        f"Игровой ник: {user_link}"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅", callback_data=f"approve:{update.effective_user.id}:{user_data['nickname']}"),
            InlineKeyboardButton("❌", callback_data=f"reject:{update.effective_user.id}:{user_data['nickname']}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id, 
            text=f"Новая анкета:\n{survey_result}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    await update.message.reply_text(
        'Спасибо за заполнение анкеты! 👍\n\n'
        'Ваша заявка отправлена администраторам на рассмотрение. '
        'Пожалуйста, ожидайте решения. Вы получите уведомление, когда заявка будет рассмотрена.'
    )
    return ConversationHandler.END

async def other_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['rules_acknowledged'] = "Да"
    await update.message.reply_text('Сколько вам лет?')
    return AGE

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        query = update.callback_query
        await query.answer()

        data = query.data.split(':')
        action = data[0]
        admin_name = ADMIN_NAMES.get(query.from_user.id, "Неизвестный администратор")

        if action == "rules":
            response = data[1]
            if response == "yes":
                context.user_data['rules_acknowledged'] = "Да"
                await query.edit_message_text(text="Вы согласились с правилами. Сколько вам лет?")
                return AGE
            else:
                await query.edit_message_text(
                    text="Вы не согласились с правилами. Регистрация отменена. "
                         "Если вы передумаете, введите /start, чтобы попробовать снова."
                )
                return ConversationHandler.END

        if action in ["approve", "reject"]:
            user_id = int(data[1])
            nickname = data[2]

            # Создаем ссылку на профиль игрока
            player_link = f'<a href="tg://user?id={user_id}">{nickname}</a>'

            # Сохраняем информацию о заявке
            applications = load_applications()
            if str(user_id) not in applications:
                applications[str(user_id)] = []
            
            # Проверяем, не была ли заявка уже обработана
            user_apps = applications.get(str(user_id), [])
            if user_apps and user_apps[-1].get('nickname') == nickname and user_apps[-1].get('status') in ['approved', 'rejected']:
                await query.edit_message_text(
                    text=f"Эта заявка уже была {'одобрена' if user_apps[-1]['status'] == 'approved' else 'отклонена'} администратором {user_apps[-1]['admin']}.",
                    parse_mode='HTML'
                )
                return
            
            applications[str(user_id)].append({
                'date': datetime.now().isoformat(),
                'status': 'approved' if action == 'approve' else 'rejected',
                'nickname': nickname,
                'admin': admin_name
            })
            save_applications(applications)

            if action == "approve":
                # Добавление игрока в whitelist через RCON
                rcon_success = False
                try:
                    with MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
                        # Добавляем игрока в whitelist
                        response = mcr.command(f"comfywhitelist add {nickname}")
                        print(f"RCON ответ: {response}")  # Для отладки
                        rcon_success = True
                except Exception as e:
                    print(f"Ошибка RCON подключения: {e}")
                    await query.edit_message_text(
                        text=f"Ошибка при добавлении игрока {player_link} в whitelist: {str(e)}", 
                        parse_mode='HTML'
                    )
                
                if rcon_success:
                    # Отправляем сообщение игроку
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"Здравствуйте, {player_link}! Ваша заявка одобрена, и вы добавлены в вайтлист сервера.\n\n"
                                "IP и другую информацию о сервере можно найти в нашем тг канале: https://t.me/unikMC\n\n"
                                "Либо на дискорд сервере https://discord.com/invite/XBWNN58qJb\n\n"
                                "Хорошей игры и не нарушайте правила сервера!"
                            ),
                            parse_mode='HTML'
                        )
                        # Обновляем сообщение с кнопками
                        await query.edit_message_text(
                            text=f"✅ Анкета игрока {player_link} одобрена и добавлена в whitelist.",
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        print(f"Ошибка отправки сообщения: {e}")

            elif action == "reject":
                try:
                    # Отправляем сообщение игроку об отклонении
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"К сожалению, {player_link}, ваша заявка была отклонена. Вы сможете подать новую заявку через 7 дней.",
                        parse_mode='HTML'
                    )
                    # Обновляем сообщение с кнопками
                    await query.edit_message_text(
                        text=f"❌ Анкета игрока {player_link} отклонена.",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Ошибка отправки сообщения об отклонении: {e}")

            # Уведомление другим администраторам и удаление кнопок
            try:
                for admin_id in ADMIN_IDS:
                    if admin_id != query.from_user.id:
                        try:
                            # Находим сообщение с анкетой у других администраторов
                            async for message in context.bot.get_chat(admin_id).iter_messages(limit=50):
                                if (
                                    message.reply_markup and 
                                    isinstance(message.reply_markup, InlineKeyboardMarkup) and
                                    any(f":{user_id}:{nickname}" in button.callback_data for row in message.reply_markup.inline_keyboard for button in row)
                                ):
                                    # Обновляем сообщение без кнопок
                                    await message.edit_text(
                                        text=f"{admin_name} {'✅ одобрил' if action == 'approve' else '❌ отклонил'} анкету {player_link}.",
                                        parse_mode='HTML'
                                    )
                                    break
                        except Exception as e:
                            print(f"Ошибка при обновлении сообщения у администратора {admin_id}: {e}")
            except Exception as e:
                print(f"Ошибка отправки уведомлений администраторам: {e}")

    except Exception as e:
        print(f"Общая ошибка в обработчике кнопок: {e}")
        try:
            await query.edit_message_text(
                text="Произошла ошибка при обработке заявки. Пожалуйста, попробуйте позже.",
                parse_mode='HTML'
            )
        except:
            pass

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Анкета отменена.')
    return ConversationHandler.END

async def main():
    # Создаем приложение с увеличенными таймаутами
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30.0)  # Увеличиваем таймаут подключения
        .read_timeout(30.0)     # Увеличиваем таймаут чтения
        .write_timeout(30.0)    # Увеличиваем таймаут записи
        .pool_timeout(30.0)     # Увеличиваем таймаут пула
        .get_updates_read_timeout(30.0)  # Увеличиваем таймаут получения обновлений
        .build()
    )
    
    # Пытаемся удалить webhook с повторными попытками
    max_retries = 3
    retry_delay = 5  # секунд
    
    for attempt in range(max_retries):
        try:
            await application.bot.delete_webhook()
            break
        except telegram.error.TimedOut:
            if attempt < max_retries - 1:
                print(f"Таймаут при удалении webhook. Повторная попытка через {retry_delay} секунд...")
                await asyncio.sleep(retry_delay)
            else:
                print("Не удалось удалить webhook после всех попыток. Продолжаем без удаления...")
        except Exception as e:
            print(f"Ошибка при удалении webhook: {e}")
            break
    
    # Добавляем обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            RULES: [CallbackQueryHandler(button, pattern='^rules:')],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nickname)],
            OTHER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_info)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_chat=True,
        per_message=False,
        per_user=True
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button, pattern='^(approve|reject):'))
    
    # Запускаем бота с автоматическими повторными попытками при ошибках
    while True:
        try:
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            print("Попытка переподключения через 10 секунд...")
            await asyncio.sleep(10)
            continue

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())