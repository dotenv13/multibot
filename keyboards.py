from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def providers_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Trust", callback_data="prov_trust")],
        [InlineKeyboardButton("Bybit", callback_data="prov_bybit")],
    ])

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Баланс", callback_data="mode_balance")],
        [InlineKeyboardButton("📋 Стейкинг (список)", callback_data="mode_staking_list")],
        [InlineKeyboardButton("📈 Активный стейкинг", callback_data="mode_staking_active")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ В меню режимов", callback_data="back_to_menu")],
        [InlineKeyboardButton("🏦 К выбору биржи", callback_data="back_to_providers")],
    ])
