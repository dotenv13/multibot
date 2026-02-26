from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from keyboadrs import main_menu_keyboard, back_keyboard
from balance_handler import handle_balance_mode
from staking_list_handler import handle_staking_list_mode
from staking_active_handler import handle_staking_active_mode

# ТОКЕН БОТА
BOT_TOKEN = "8349418037:AAHJaMQfa9ryWJCYXgHjUDUQwfsM67tevS0"

# Режимы
MODE_BALANCE = "balance"
MODE_STAKING_LIST = "staking_list"
MODE_STAKING_ACTIVE = "staking_active"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    text = (
        "Выбери режим:\n"
        "• 💰 Баланс — отрисовка баланса по твоему вводу\n"
        "• 📋 Стейкинг (список) — список монет с процентами\n"
        "• 📈 Активный стейкинг — отрисовка стейкинга конкретной монеты\n\n"
        "Нажми нужную кнопку ниже 👇"
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def on_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_menu":
        context.user_data.clear()

        # Отправляем полностью новый стартовый экран
        await query.message.chat.send_message(
            text=(
                "Выбери режим:\n"
                "• 💰 Баланс — отрисовка баланса по твоему вводу\n"
                "• 📋 Стейкинг (список) — список монет с процентами\n"
                "• 📈 Активный стейкинг — отрисовка стейкинга конкретной монеты\n\n"
                "Нажми нужную кнопку ниже 👇"
            ),
            reply_markup=main_menu_keyboard()
        )
        return

    if data == "mode_balance":
        context.user_data["mode"] = MODE_BALANCE
        msg = (
            "💰 Баланс\n\n"
            "Формат ввода (сайт монета сеть количество):\n"
            "Пример:\n"
            "```text\n"
            "coinpaprika.info\n"
            "usdt eth 2\n"
            "```\n"
        )
        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard())
        return

    if data == "mode_staking_list":
        context.user_data["mode"] = MODE_STAKING_LIST
        msg = (
            "📋 Стейкинг (список)\n\n"
            "Формат ввода (сайт, номер строки(1–7), монета, процент):\n"
            "```text\n"
            "coinpaprika.info\n"
            "1 ETH 3.62\n"
            "2 OP 12.1\n"
            "3 STRK 15.21\n"
            "```\n"
        )
        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard())

    if data == "mode_staking_active":
        context.user_data["mode"] = MODE_STAKING_ACTIVE
        msg = (
            "📈 Активный стейкинг\n\n"
            "Отправь 8 строк в таком формате:\n\n"
            "```text\n"
            "coinpaprika.info\n"
            "Ethereum (ETH)\n"
            "10 ETH\n"
            "0 ETH\n"
            "0.01 ETH\n"
            "100%\n"
            "~30 days\n"
            "29d 19h\n"
            "Trust Nodes\n"
            "```\n"
        )
        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard())


# =============================
#   ОБЩИЙ ОБРАБОТЧИК ТЕКСТА
# =============================

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if mode == MODE_BALANCE:
        await handle_balance_mode(update, context)
    elif mode == MODE_STAKING_LIST:
        await handle_staking_list_mode(update, context)
    elif mode == MODE_STAKING_ACTIVE:
        await handle_staking_active_mode(update, context)
    else:
        # Режим не выбран — предложить меню
        await update.message.reply_text(
            "Сначала выбери режим 👇",
            reply_markup=main_menu_keyboard()
        )

# =============================
#           MAIN
# =============================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_menu_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling()


if __name__ == "__main__":
    main()
