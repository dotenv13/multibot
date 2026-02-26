from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Баланс", callback_data="mode_balance")],
        [InlineKeyboardButton("📋 Стейкинг (список)", callback_data="mode_staking_list")],
        [InlineKeyboardButton("📈 Активный стейкинг", callback_data="mode_staking_active")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("В главное меню", callback_data="back_to_menu")]
    ])
