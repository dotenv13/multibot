import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from keyboards import back_keyboard
from binance.spot import Spot

# =============================
#        ПУТИ
# =============================

EARN_TEMPLATE = "imageTemplates/trust/TemplateEarn.jpg"
SCREENS_DIR = "screens"

FONT_SF_REGULAR = "fonts/SF-Pro-Display-Regular.otf"
FONT_SF_SEMI    = "fonts/SF-Pro-Display-Semibold.otf"
FONT_SF_BOLD    = "fonts/SF-Pro-Display-Bold.otf"
FONT_SF_MEDIUM  = "fonts/SF-Pro-Display-Medium.otf"

# =============================
#        КООРДИНАТЫ
# =============================

IMAGE_WIDTH  = 739
IMAGE_HEIGHT = 1600

# Время (левый верхний угол)
TIME_X, TIME_Y = 59, 47

# Иконка монеты
ICON_SIZE = 75
NET_SIZE  = 36
ICON_X    = 61

# Стейблкоин Earn — top Y каждой иконки
STABLE_ICON_TOP = [479, 616, 752]

# Нативный стейкинг — top Y каждой иконки
NATIVE_ICON_TOP = [1057, 1194, 1330]

# X тикера
TICKER_X = 160

DO_X      = 440   # подбери по шаблону
PERCENT_X = 480   # подбери по шаблону

# =============================
#        ЦВЕТА
# =============================

COLOR_TICKER  = "#242426"
COLOR_BLACK   = "#111111"
COLOR_GREY    = "#777777"
COLOR_PERCENT = "#7B4FE9"
COLOR_GREEN   = "#52a462"
COLOR_RED     = "#e4566c"

NETWORK_ICON_MAP = {
    "TRX": "TRX", "TRON": "TRX",
    "ERC20": "ETH", "ETH": "ETH",
    "BEP20": "BEP20", "BSC": "BEP20",
    "ARB": "ARB", "ARBITRUM": "ARB",
    "SOL": "SOL",
}

# =============================
#        ГЕНЕРАЦИЯ
# =============================

def draw_coin_row(draw, image, icon_top, sym, network, percent_str, font_ticker,
                  font_text, font_percent, font_price,
                  percent_color=COLOR_PERCENT, percent_offset=370,
                  price_text=None, change_str=None, change_color=COLOR_GREY,
                  ticker_offset=25,   # только тикер
                  percent_y_offset=25,  # только процент
                  price_y_offset=61):   # только цена/изменение
    """Рисует одну строку монеты. Тикер, процент и цена двигаются независимо."""

    # Иконка монеты
    icon_path = f"coins/rounded_{sym}.png"
    if os.path.exists(icon_path):
        icon = Image.open(icon_path).convert("RGBA")
        icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
        icon = icon.filter(ImageFilter.SMOOTH)
        image.paste(icon, (ICON_X, icon_top), icon)

    # Иконка сети (правый нижний угол)
    if network:
        net_key = NETWORK_ICON_MAP.get(network.upper())
        if net_key:
            net_path = f"coins/networks/{net_key}.png"
            if os.path.exists(net_path):
                net_icon = Image.open(net_path).convert("RGBA")
                net_icon = net_icon.resize((NET_SIZE, NET_SIZE), Image.Resampling.LANCZOS)
                net_x = ICON_X + ICON_SIZE - NET_SIZE + 6
                net_y = icon_top + ICON_SIZE - NET_SIZE + 6
                image.paste(net_icon, (net_x, net_y), net_icon)

    # Три независимых Y
    ticker_y  = icon_top + ticker_offset    # тикер (ETH, BNB...)
    percent_y = icon_top + percent_y_offset  # процент справа
    price_y   = icon_top + price_y_offset    # цена и изменение

    # Тикер
    draw.text((TICKER_X, ticker_y), sym, font=font_ticker, fill=COLOR_TICKER, anchor="lt")

    # Цена + изменение (только для нативного)
    if price_text:
        price_w = draw.textlength(price_text, font=font_price)
        draw.text((TICKER_X, price_y), price_text, font=font_price, fill=COLOR_GREY, anchor="lt")
        if change_str:
            draw.text((TICKER_X + price_w + 8, price_y), change_str, font=font_price, fill=change_color, anchor="lt")

    # "до"
    draw.text((DO_X, percent_y + 8), "до", font=font_text, fill="#444444", anchor="lt")

    # процент
    draw.text((PERCENT_X, percent_y), percent_str + "%", font=font_percent, fill=percent_color, anchor="lt")

    # "годовых" — после процента динамически
    percent_w = draw.textlength(percent_str + "%", font=font_percent)
    draw.text((PERCENT_X + percent_w + 8, percent_y + 8), "годовых", font=font_text, fill="#444444", anchor="lt")


def generate_earn_card(
    stable_coins: list,
    native_coins: list,
    output_path: str,
):
    img = Image.open(EARN_TEMPLATE).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Шрифты
    font_time      = ImageFont.truetype(FONT_SF_SEMI,    30)
    font_ticker    = ImageFont.truetype(FONT_SF_SEMI,    31)
    font_text      = ImageFont.truetype(FONT_SF_SEMI,    24)
    font_percent   = ImageFont.truetype(FONT_SF_BOLD,    31)
    font_percent_n = ImageFont.truetype(FONT_SF_SEMI,    31)
    font_price     = ImageFont.truetype(FONT_SF_BOLD, 23)

    # Время
    draw.text((TIME_X, TIME_Y), datetime.now().strftime("%H:%M"),
              font=font_time, fill=COLOR_BLACK, anchor="lm")

    # Стейблкоин Earn — тикер и процент на одном Y=25, цены нет
    for i, (sym, network, pct) in enumerate(stable_coins[:3]):
        draw_coin_row(draw, img, STABLE_ICON_TOP[i], sym, network, pct,
                      font_ticker, font_text, font_percent, font_price,
                      ticker_offset=25,
                      percent_y_offset=25)

    # Нативный стейкинг — тикер выше (offset=20), процент на 25, цена на 61
    client = Spot()
    for i, (sym, network, pct) in enumerate(native_coins[:3]):
        try:
            if sym == "USDT":
                price = 1.0
                change = 0.0
            else:
                ticker_data = client.ticker_24hr(symbol=sym + "USDT")
                price = float(ticker_data["lastPrice"])
                change = float(ticker_data["priceChangePercent"])
        except Exception:
            price = 0.0
            change = 0.0

        price_str = f"{price:,.2f}".replace(",", " ").replace(".", ",") + " $"

        if change > 0:
            change_str = f"+{change:.2f}".replace(".", ",") + "%"
            change_color = COLOR_GREEN
        elif change < 0:
            change_str = f"{change:.2f}".replace(".", ",") + "%"
            change_color = COLOR_RED
        else:
            change_str = None
            change_color = COLOR_GREY

        draw_coin_row(draw, img, NATIVE_ICON_TOP[i], sym, network, pct,
                      font_ticker, font_text, font_percent_n, font_price,
                      percent_color=COLOR_BLACK, percent_offset=368,
                      price_text=price_str, change_str=change_str, change_color=change_color,
                      ticker_offset=10,      # ← только тикер выше
                      percent_y_offset=25,   # ← процент не трогаем
                      price_y_offset=48)     # ← цена под тикером

    os.makedirs(SCREENS_DIR, exist_ok=True)
    img.convert("RGB").save(output_path, format="JPEG", quality=95)


# =============================
#        TELEGRAM HANDLER
# =============================

async def handle_earn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Формат ввода — 6 строк:

    USDT ETH 4.5
    USDC ETH 3.4
    USDT TRX 1.7
    ETH 2.6
    BNB 1.0
    SOL 6.6

    Первые 3 — Стейблкоин Earn
    Последние 3 — Нативный стейкинг (цена подтягивается автоматически)
    """
    text = update.message.text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    if len(lines) != 6:
        await update.message.reply_text(
            f"❗ Ожидаю 6 строк, получил: {len(lines)}\n\n"
            "Формат:\n"
            "```\n"
            "USDT ETH 4.5\n"
            "USDC ETH 3.4\n"
            "USDT TRX 1.7\n"
            "ETH 2.6\n"
            "BNB 1.0\n"
            "SOL 6.6\n"
            "```\n"
            "Первые 3 — Стейблкоин Earn\n"
            "Последние 3 — Нативный стейкинг\n"
            "Сеть опциональна",
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )
        return

    def parse_line(line):
        parts = line.split()
        try:
            if len(parts) == 2:
                return parts[0].upper(), None, parts[1]
            elif len(parts) >= 3:
                return parts[0].upper(), parts[1].upper(), parts[2]
        except Exception:
            pass
        return None

    stable_coins = []
    native_coins = []

    for line in lines[:3]:
        parsed = parse_line(line)
        if parsed:
            stable_coins.append(parsed)

    for line in lines[3:]:
        parsed = parse_line(line)
        if parsed:
            native_coins.append(parsed)

    username = update.message.from_user.username or "user"
    ts = int(datetime.now().timestamp())
    output_path = os.path.join(SCREENS_DIR, f"earn_{username}_{ts}.jpg")

    try:
        generate_earn_card(stable_coins, native_coins, output_path)
        with open(output_path, "rb") as f:
            await update.message.reply_photo(f, reply_markup=back_keyboard())
    except Exception as e:
        await update.message.reply_text(
            f"⚠ Ошибка генерации: {e}",
            reply_markup=back_keyboard()
        )