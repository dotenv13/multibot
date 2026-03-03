import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from PIL import Image, ImageDraw, ImageFont
from keyboards import back_keyboard

# =============================
#        ПУТИ
# =============================

STAKING_ACTIVE_TEMPLATE = "imageTemplates/bybit/TemplateActiveStaking.jpg"
SCREENS_DIR = "screens"

FONT_SF_REGULAR  = "fonts/SF-Pro-Display-Regular.otf"
FONT_SF_SEMI     = "fonts/SF-Pro-Display-Semibold.otf"

# =============================
#        КООРДИНАТЫ
# =============================

IMAGE_WIDTH = 591

# Время (левый верхний угол)
TIME_X, TIME_Y = 44, 36          # anchor="lm"

# URL сайта (после иконки замка)
SITE_X, SITE_Y = 125, 108        # anchor="lm"

# Калькулятор — левое число (Инвестировать)
CALC_L_X = 50
CALC_L_Y = 610                   # anchor="lt"

# Калькулятор — правое число (Прибыль 30D)
CALC_R_X = 340
CALC_R_Y = 610                   # anchor="lt"

# Таблица «Обзор активов» — Y центра каждой строки
# Порядок: TVL, Проект, Заморожено, Доход, Минимальная сумма, Осталось
TABLE_Y = [812, 855, 904, 948, 990, 1030]

# Правый край таблицы
TABLE_RIGHT_X = 567

# =============================
#        ЦВЕТА
# =============================

COLOR_WHITE = "white"
COLOR_GREY  = "#5f5f5f"   # сайт

# =============================
#        ГЕНЕРАЦИЯ
# =============================

def generate_staking_active_card(
    site_text: str,       # URL сайта (уже с https://)
    invest_val: str,      # Левое число калькулятора (Инвестировать)
    profit_val: str,      # Правое число калькулятора (Прибыль 30D)
    tvl: str,             # TVL
    project: str,         # Проект
    frozen: str,          # Заморожено
    income: str,          # Доход
    min_amount: str,      # Минимальная сумма
    time_left: str,       # Осталось
    output_path: str,
):
    img = Image.open(STAKING_ACTIVE_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Шрифты
    font_time  = ImageFont.truetype(FONT_SF_SEMI,    23)
    font_site  = ImageFont.truetype(FONT_SF_REGULAR, 19)
    font_calc  = ImageFont.truetype(FONT_SF_REGULAR,    22)   # числа калькулятора
    font_table = ImageFont.truetype(FONT_SF_REGULAR, 23)   # значения таблицы

    # Время
    draw.text(
        (TIME_X, TIME_Y),
        datetime.now().strftime("%H:%M"),
        font=font_time,
        fill=COLOR_WHITE,
        anchor="lm"
    )

    # URL сайта
    draw.text(
        (SITE_X, SITE_Y),
        site_text,
        font=font_site,
        fill=COLOR_GREY,
        anchor="lm"
    )

    # Калькулятор — левое число
    draw.text(
        (CALC_L_X, CALC_L_Y),
        invest_val,
        font=font_calc,
        fill=COLOR_WHITE,
        anchor="lt"
    )

    # Калькулятор — правое число
    draw.text(
        (CALC_R_X, CALC_R_Y),
        profit_val,
        font=font_calc,
        fill=COLOR_WHITE,
        anchor="lt"
    )

    # Таблица — значения по правому краю
    table_values = [tvl, project, frozen, income, min_amount, time_left]
    for value, y in zip(table_values, TABLE_Y):
        text_w = draw.textlength(value, font=font_table)
        draw.text(
            (TABLE_RIGHT_X - text_w, y),
            value,
            font=font_table,
            fill=COLOR_WHITE
        )

    os.makedirs(SCREENS_DIR, exist_ok=True)
    img.save(output_path, format="JPEG", quality=95)


# =============================
#        TELEGRAM HANDLER
# =============================

async def handle_staking_active_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Формат ввода — 9 строк:

    bybit-web3.link
    1000.00
    41.50
    $202.34M
    renzo
    100 ALGO
    0.27666666 ALGO
    0.01 ALGO
    28d 0h
    """
    text = update.message.text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    if len(lines) != 9:
        await update.message.reply_text(
            f"❗ Ожидаю 9 строк, получил: {len(lines)}\n\n"
            "Формат:\n"
            "```\n"
            "bybit-web3.link\n"
            "1000.00\n"
            "41.50\n"
            "$202.34M\n"
            "renzo\n"
            "100 ALGO\n"
            "0.27666666 ALGO\n"
            "0.01 ALGO\n"
            "28d 0h\n"
            "```",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        return

    site_text  = "https://" + lines[0]
    try:
        invest_val = f"{float(lines[1].replace(',', '.')):.2f}"
        parts = invest_val.split('.')
        parts[0] = f"{int(parts[0]):,}"
        invest_val = '.'.join(parts)
    except ValueError:
        invest_val = lines[1]   # инвестировать
    profit_val = lines[2]   # прибыль 30D
    tvl        = lines[3]   # TVL
    project    = lines[4]   # Проект
    frozen     = lines[5]   # Заморожено
    income     = lines[6]   # Доход
    min_amount = lines[7]   # Минимальная сумма
    time_left  = lines[8]   # Осталось

    username = update.message.from_user.username or "user"
    ts = int(datetime.now().timestamp())
    output_path = os.path.join(SCREENS_DIR, f"stake_{username}_{ts}.jpg")

    try:
        generate_staking_active_card(
            site_text,
            invest_val, profit_val,
            tvl, project, frozen,
            income, min_amount, time_left,
            output_path
        )
        with open(output_path, "rb") as f:
            await update.message.reply_photo(f, reply_markup=back_keyboard())
    except Exception as e:
        await update.message.reply_text(
            f"⚠ Ошибка генерации: {e}",
            reply_markup=back_keyboard()
        )