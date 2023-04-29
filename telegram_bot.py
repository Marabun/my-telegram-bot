import logging
import ccxt
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Введите ваш токен бота здесь
TELEGRAM_API_TOKEN = '6057478958:AAFV9SYvTvVm_5C1LvW5aSIV_4xbHgqdKTI'

logging.basicConfig(level=logging.INFO)

CHOOSE_CRYPTO, SETTING_ALERT, ENTER_PERCENTAGE, ENTER_SUM, ENTER_PRICE = range(5)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    context.bot.send_message(
        chat_id=user.id,
        text='Привет! Я криптовалютный бот. Я помогу вам следить за криптовалютами и получать оповещения.'
    )
    main_menu(update, context)

# Код для основного меню тут

# Конфигурация обработчика разговоров тут

def main():
    updater = Updater(TELEGRAM_API_TOKEN)

    # Регистрация обработчиков тут

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
def main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton('Цена', callback_data='price'),
            InlineKeyboardButton('Оповещение', callback_data='alert'),
        ],
        [
            InlineKeyboardButton('Настройки', callback_data='settings'),
            InlineKeyboardButton('О программе', callback_data='about'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите действие:', reply_markup=reply_markup)

def price(update: Update, context: CallbackContext):
    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        context.bot.send_message(
            chat_id=update.effective_user.id,
            text=f"Текущая цена BTC: {price:.2f} USDT",
        )
    except ccxt.BaseError as e:
        logging.error(f"Ошибка API при вызове функции price: {e}")
        context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Извините, произошла ошибка при получении данных с биржи. Пожалуйста, попробуйте позже.",
        )
    # Детали цены добавлю в следующем сообщении

# В конфигурации обработчика разговоров добавьте следующую строку:
price_handler = CommandHandler('price', price)

# Затем зарегистрируйте обработчик в функции main():
updater.dispatcher.add_handler(price_handler)
def price_details(update: Update, context: CallbackContext):
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker('BTC/USDT')
    price_change_percentage_24h = ticker['percentage']
    price_change_24h = ticker['change']
    volume_24h = ticker['baseVolume']
    high_24h = ticker['high']
    low_24h = ticker['low']

    details_text = f"""
Детали цены BTC:
Биржа: Binance
Изменение цены за 24 часа: {price_change_24h:+.2f} USDT ({price_change_percentage_24h:+.2f}%)
24-часовой объем торгов: {volume_24h:.2f} BTC
Максимальная цена за 24 часа: {high_24h:.2f} USDT
Минимальная цена за 24 часа: {low_24h:.2f} USDT
"""

    update.callback_query.answer()
    context.bot.send_message(chat_id=update.effective_user.id, text=details_text)

def button_callback(update: Update, _: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "price":
        price(update, _)
    # Исходный код для других кнопок будет добавлен позже

# Зарегистрируйте обратный вызов кнопки в функции main()
updater.dispatcher.add_handler(CallbackQueryHandler(button_callback))
def alert_start(update: Update, context: CallbackContext):
    update.callback_query.answer()
    keyboard = [
        [
            InlineKeyboardButton('Назад', callback_data='main_menu'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Введите ваш новый тревожный процент с использованием формата '+/-X%', например: '+5%' или '-3%'.",
        reply_markup=reply_markup,
    )

    return SETTING_ALERT

def alert_set_percentage(update: Update, context: CallbackContext):
    query = update.message.text
    if query.endswith('%') and query[:-1].replace('-', '').replace('+', '').isdigit():
        percentage = int(query[:-1])
        context.user_data['alert_percentage'] = percentage
        update.message.reply_text(f'Тревожный процент установлен на: {percentage}%')
    else:
        update.message.reply_text('Неверный формат процента. Пожалуйста, используйте формат "+X%" или "-X%", где X - число.')

# Регистрация состояний и обработчиков разговора в обработчике беседы.
alert_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(alert_start, pattern='^alert$')],
    states={
        SETTING_ALERT: [
            MessageHandler(Filters.text & ~Filters.command, alert_set_percentage),
        ],
    },
    fallbacks=[CommandHandler('stop', stop_nested)],
)

# Зарегистрируйте alert_conv_handler в функции main()
updater.dispatcher.add_handler(alert_conv_handler)
def alert_set_sum(update: Update, context: CallbackContext):
    query = update.message.text
    try:
        sum_value = float(query)
        context.user_data["alert_sum"] = sum_value
        update.message.reply_text(f"Тревога будет активирована на сумме: {sum_value} USDT")
    except ValueError:
        update.message.reply_text("Неверный формат суммы. Пожалуйста, введите число.")

def stop_nested(update: Update, context: CallbackContext):
    context.user_data.clear()

    update.message.reply_text("Настройка оповещений отменена.")
    main_menu(update, context)

    return ConversationHandler.END

# Регистрация состояния SETTING_SUM и обработчика в alert_conv_handler.
alert_conv_handler.states[SETTING_ALERT].append(MessageHandler(Filters.text & ~Filters.command, alert_set_sum))

# Измените список fallbacks для исключения stop_conv_handler:
alert_conv_handler.fallbacks.append(CommandHandler("stop", stop_nested))
import time

def check_alerts(context: CallbackContext):
    if "alerts" not in context.bot_data:
        context.bot_data["alerts"] = {}

    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker("BTC/USDT")
        price = ticker["last"]
    except ccxt.BaseError as e:
        logging.error(f"Ошибка API при вызове функции check_alerts: {e}")
        return

    for user_id, user_data in context.bot_data["alerts"].items():
        percentage = user_data.get("alert_percentage")
        alert_sum = user_data.get("alert_sum")
        last_alert = user_data.get("last_alert", 0)

        if percentage is not None and alert_sum is not None:
            price_change = (price - last_alert) / last_alert * 100

            if abs(price_change) >= percentage:
                user_data["last_alert"] = price
                direction = "увеличилась" if price_change > 0 else "уменьшилась"
                context.bot.send_message(
                    chat_id=user_id,
                    text=f"Цена BTC {direction} на {abs(price_change):.2f}%.\nТекущая цена: {price:.2f} USDT\nСумма оповещения: {alert_sum:.2f} USDT",
                )


if __name__ == "__main__":
    # Инициализируйте задание для периодической проверки оповещений.
    job_queue = updater.job_queue
    job_queue.run_repeating(check_alerts, interval=60, first=0)
    # Оставьте эту строку вконце файла.
    main()
