from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from keyboards import providers_keyboard, main_menu_keyboard, back_keyboard

from balance_handler import handle_balance_mode as trust_balance
from staking_list_handler import handle_staking_list_mode as trust_staking_list
from staking_active_handler import handle_staking_active_mode as trust_staking_active_list

from bybit_balance_handler import handle_balance_mode as bybit_balance
from bybit_staking_list_handler import handle_staking_list_mode as bybit_staking_list
from bybit_staking_active_handler import handle_staking_active_mode as bybit_staking_active_list

from earn_handler import handle_earn_mode

# ТОКЕН БОТА
BOT_TOKEN = "8349418037:AAHJaMQfa9ryWJCYXgHjUDUQwfsM67tevS0"

# Провайдеры
PROV_TRUST = "trust"
PROV_BYBIT = "bybit"

# Режимы
MODE_BALANCE = "balance"
MODE_STAKING_LIST = "staking_list"
MODE_STAKING_ACTIVE = "staking_active"
MODE_EARN = "earn"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Выбери кошелёк/биржу 👇",
        reply_markup=providers_keyboard()
    )


async def on_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- выбор провайдера ---
    if data == "prov_trust":
        context.user_data["provider"] = PROV_TRUST
        context.user_data["mode"] = None
        await query.message.reply_text(
            "Выбран: Trust ✅\n\nТеперь выбери режим 👇",
            reply_markup=main_menu_keyboard()
        )
        return

    if data == "prov_bybit":
        context.user_data["provider"] = PROV_BYBIT
        context.user_data["mode"] = None
        await query.message.reply_text(
            "Выбран: Bybit ✅\n\nТеперь выбери режим 👇",
            reply_markup=main_menu_keyboard()
        )
        return

    if data == "back_to_menu":
        # назад к меню режимов (провайдер сохраняем)
        context.user_data["mode"] = None
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

    if data == "back_to_providers":
        context.user_data.clear()
        await query.message.chat.send_message(
            text="Выбери кошелёк/биржу 👇",
            reply_markup=providers_keyboard()
        )
        return

    if data == "mode_balance":
        context.user_data["mode"] = MODE_BALANCE
        provider = context.user_data.get("provider")

        if provider == PROV_BYBIT:
            msg = (
                "💰 Баланс\n\n"
                "Формат ввода (сайт монета сеть количество):\n"
                "Пример:\n"
                "```text\n"
                "bybit-web3.link\n"
                "BTC 0.5\n"
                "ETH 2\n\n"
                "Или с сетью:\n"
                "USDT TRX 1500"
                "```"
            )
        else:  # PROV_TRUST
            msg = (
                "💰 Баланс\n\n"
                "Формат ввода (сайт монета сеть количество):\n"
                "Пример:\n"
                "```text\n"
                "coinpaprika.info\n"
                "BTC 0.5\n"
                "ETH 2\n\n"
                "Или с сетью:\n"
                "USDT TRX 1500"
                "```\n"
            )
        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard())

    if data == "mode_staking_list":
        context.user_data["mode"] = MODE_STAKING_LIST
        provider = context.user_data.get("provider")

        if provider == PROV_BYBIT:
            msg = (
                "📋 Стейкинг (список)\n\n"
                "Формат ввода (сайт, номер строки(1–5), монета, процент):\n"
                "```text\n"
                "bybit-web3.link\n"
                "1 ETH 2.8\n"
                "2 ALGO 4.12"
                "```"
            )
        else:  # PROV_TRUST
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
        provider = context.user_data.get("provider")

        if provider == PROV_BYBIT:
            msg = (
                "📈 Активный стейкинг\n\n"
                "Отправь 9 строк:\n"
                "```text\n"
                "bybit-web3.link\n"
                "1000.00\n"
                "41.50\n"
                "$202.34M\n"
                "renzo\n"
                "100 ALGO\n"
                "0.27666666 ALGO\n"
                "0.01 ALGO\n"
                "28d 0h\n"
                "```"
            )
        else:  # PROV_TRUST
            msg = (
                "📈 Активный стейкинг\n\n"
                "Отправь 9 строк:\n"
                "```text\n"
                "coinpaprika.info\n"
                "Ethereum (ETH)\n"
                "10 ETH\n"
                "0 ETH\n"
                "0.01 ETH\n"
                "100%\n"
                "~30 days\n"
                "29d 19h\n"
                "Trust Nodes"
                "```"
            )
        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard())

    if data == "mode_earn":
        context.user_data["mode"] = MODE_EARN
        msg = (
            "💸 Заработок\n\n"
            "Отправь 6 строк:\n"
            "```text\n"
            "USDT ETH 4.5\n"
            "USDC ETH 3.4\n"
            "USDT TRX 1.7\n"
            "ETH 2.6\n"
            "BNB 1.0\n"
            "SOL 6.6\n"
            "```"
        )
        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard())

# =============================
#   ОБЩИЙ ОБРАБОТЧИК ТЕКСТА
# =============================

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    provider = context.user_data.get("provider")
    mode = context.user_data.get("mode")

    if not provider:
        await update.message.reply_text("Сначала выбери кошелёк/биржу 👇", reply_markup=providers_keyboard())
        return

    if not mode:
        await update.message.reply_text("Сначала выбери режим 👇", reply_markup=main_menu_keyboard())
        return

    if provider == PROV_TRUST:
        if mode == MODE_BALANCE:
            await trust_balance(update, context)
        elif mode == MODE_STAKING_LIST:
            await trust_staking_list(update, context)
        elif mode == MODE_STAKING_ACTIVE:
            await trust_staking_active_list(update, context)
        elif mode == MODE_EARN:
            await handle_earn_mode(update, context)
        else:
            await update.message.reply_text("Неизвестный режим.", reply_markup=providers_keyboard())
        return

    if provider == PROV_BYBIT:
        if mode == MODE_BALANCE:
            await bybit_balance(update, context)
        elif mode == MODE_STAKING_LIST:
            await bybit_staking_list(update, context)
        elif mode == MODE_STAKING_ACTIVE:
            await bybit_staking_active_list(update, context)
        elif mode == MODE_EARN:
            await update.message.reply_text("⚠ Режим недоступен для Bybit.", reply_markup=providers_keyboard())
        else:
            await update.message.reply_text("Неизвестный режим.", reply_markup=providers_keyboard())
        return

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
