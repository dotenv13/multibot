import os
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from data import crypto_dict
from keyboards import back_keyboard

# =============================
#   ДАННЫЕ ДЛЯ СТЕЙКИНГ-ЛИСТА
# =============================

STAKING_LIST_TEMPLATE = "imageTemplates/bybit/TemplateStaking.jpg"

FONT_SF_REGULAR = "fonts/SF-Pro-Display-Regular.otf"
FONT_SF_MEDIUM  = "fonts/SF-Pro-Display-Medium.otf"
FONT_SF_SEMI    = "fonts/SF-Pro-Display-Semibold.otf"
font_symbol = ImageFont.truetype(FONT_SF_REGULAR, 23)
font_name    = ImageFont.truetype(FONT_SF_MEDIUM, 22)
font_percent = ImageFont.truetype(FONT_SF_REGULAR, 23)
font_mrp     = ImageFont.truetype(FONT_SF_REGULAR, 23)
font_time   = ImageFont.truetype(FONT_SF_SEMI, 23)

START_Y = 700
ROW_GAP = 74   # ← увеличивай / уменьшай тут

FONT_ROBOTO = "fonts/Roboto-Regular.ttf"
FONT_ROBOTO_SEMI = "fonts/Roboto-SemiBold.ttf"
FONT_DINPRO = "fonts/dinpro_medium.otf"
FONT_DINPRO_BOLD = "fonts/dinpro_bold.otf"
SCREENS_DIR = "screens"

percent_y_staking = [START_Y + i * ROW_GAP for i in range(10)]

default_percents = ("3.2", "4.3", "3.8", "4.53", "4.13",
                    "3.52", "5.1", "4.9", "4.41", "5.21")
default_coins = ("ETH", "BNB", "SOL", "TRX", "DOT",
                 "ATOM", "XRP", "NEAR", "SUI", "ADA")


# =============================
#   РЕЖИМ: 📋 СТЕЙКИНГ-ЛИСТ
# =============================

async def handle_staking_list_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = update.message.text.splitlines()

    if len(lines) < 2:
        await update.message.reply_text(
            "❗ Формат:\n"
            "coinpaprika.info\n"
            "1 ETH 2.8\n"
            "2 ALGO 4.12",
            reply_markup=back_keyboard()
        )
        return

    site_name = "https://" + lines[0].strip()
    strings = lines[1:]

    image = Image.open(STAKING_LIST_TEMPLATE)
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(FONT_ROBOTO, size=22)
    font_smaller = ImageFont.truetype(FONT_ROBOTO, size=20)
    font_normal = ImageFont.truetype(FONT_ROBOTO_SEMI, 24)
    font_site = ImageFont.truetype(FONT_SF_REGULAR, size=19)

    IMAGE_WIDTH = 591
    IMAGE_HEIGHT = 1280

    SITE_X = 215
    SITE_Y = 108

    # Время
    formatted_time = datetime.now().strftime("%H:%M")
    draw.text((44, 22), formatted_time, font=font_time, fill="white")

    # --- НАЗВАНИЕ САЙТА (рядом с замочком в шаблоне) ---
    draw.text((SITE_X, SITE_Y), site_name, font=font_site, fill="#5f5f5f", anchor="mm")

    # Парсим строки вида "1 ETH 3.62"
    str_matrix = {}
    for line in strings:
        s = line.split()
        if len(s) < 3:
            continue
        try:
            idx = int(s[0])
        except ValueError:
            continue
        str_matrix[idx] = (s[1], s[2])  # (COIN, PERCENT)

    try:
        for i in range(5):
            y = START_Y + i * ROW_GAP

            if i + 1 in str_matrix:
                coin_sym, percent_str = str_matrix[i + 1]
            else:
                coin_sym = default_coins[i]
                percent_str = default_percents[i]

            # --- ИКОНКА ---
            icon = Image.open(f"coins/rounded_{coin_sym}.png").convert("RGBA")
            icon = icon.resize((44, 44), Image.Resampling.LANCZOS)
            image.paste(icon, (22, y - 6), icon)

            # --- ТИКЕР ---
            draw.text(
                (78, y + 2),
                coin_sym,
                font=font_symbol,
                fill="white"
            )

            # --- ПОЛНОЕ ИМЯ ---
            #full_name = crypto_dict.get(coin_sym, coin_sym)
            #draw.text((90, y + 26), full_name, font=font_name, fill="white")

            # --- ПРОЦЕНТ ---
            percent_text = f"{percent_str}%"
            percent_box = draw.textbbox((0, 0), percent_text, font=font_percent)
            percent_w = percent_box[2] - percent_box[0]

            percent_x = IMAGE_WIDTH - 88 - percent_w
            draw.text(
                (percent_x + 10, y + 2),
                percent_text,
                font=font_percent,
                fill="white"
            )

            # --- MRP ---
            draw.text(
                (percent_x + percent_w + 16, y + 2),
                "MRP",
                font=font_mrp,
                fill="white"
            )

        os.makedirs(SCREENS_DIR, exist_ok=True)
        name = os.path.join(
            SCREENS_DIR,
            "stakinglist_" + (update.message.from_user.username or "user") + ".jpg"
        )
        image.save(name)

        await update.message.reply_photo(open(name, "rb"), reply_markup=back_keyboard())

    except FileNotFoundError:
        await update.message.reply_text("Неизвестная монета или отсутствует иконка.", reply_markup=back_keyboard())
    except Exception as e:
        await update.message.reply_text(f"⚠ Ошибка стейкинг-списка: {e}", reply_markup=back_keyboard())

