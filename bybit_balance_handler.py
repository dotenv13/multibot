import os
from datetime import datetime

from binance.spot import Spot
from telegram import Update
from telegram.ext import ContextTypes

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from keyboards import back_keyboard
from data import crypto_dict


# =============================
#        НАСТРОЙКИ
# =============================

BALANCE_TEMPLATE = "imageTemplates/bybit/TemplateBalance.jpg"
SCREENS_DIR = "screens"

FONT_DINPRO_BOLD = "fonts/dinpro_bold.otf"
FONT_SF_REGULAR = "fonts/SF-Pro-Display-Regular.otf"
FONT_SF_SEMI = "fonts/SF-Pro-Display-Semibold.otf"
FONT_SF_MEDIUM = "fonts/SF-Pro-Display-Medium.otf"

IMAGE_WIDTH = 591
IMAGE_HEIGHT = 1280

# Top Y-координата иконки каждой строки монеты (до 6 штук, иконка 45x45)
COIN_ICON_TOP_Y = (546, 634, 722, 810, 898, 986)

ICON_SIZE = 45        # размер иконки монеты
NET_SIZE = 18         # размер иконки сети

ICON_X = 20           # X левого края иконки монеты

TICKER_X = 80         # X тикера и цены (левая часть)
RIGHT_X = IMAGE_WIDTH - 18  # X правого края для выравнивания текста по правому краю

# Смещения относительно icon_top
TICKER_OFFSET_Y = -5  # тикер (крупный белый текст) от top иконки
PRICE_OFFSET_Y = 30   # цена (серый текст) от top иконки

# Время
TIME_X = 47
TIME_Y = 35           # anchor="lm"

# URL/сайт
SITE_X = 124
SITE_Y = 108          # anchor="lm"
MAX_SITE_WIDTH = RIGHT_X - SITE_X - 10

# Общий баланс
TOTAL_X = 190
TOTAL_Y = 258         # anchor="mm"

NETWORK_ICON_MAP = {
    "TRX": "TRX",
    "TRON": "TRX",
    "ERC20": "ETH",
    "ETH": "ETH",
    "BEP20": "BEP20",
    "BSC": "BEP20",
    "ARB": "ARB",
    "ARBITRUM": "ARB",
    "SOL": "SOL",
}


# =============================
#      РЕЖИМ: БАЛАНС (BYBIT)
# =============================

async def handle_balance_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # ---------- ВВОД ПОЛЬЗОВАТЕЛЯ ----------
        lines = update.message.text.splitlines()

        if len(lines) < 2:
            await update.message.reply_text(
                "❗ Формат:\n"
                "Название сайта\n"
                "BTC 0.5\n"
                "ETH 2\n\n"
                "Или с сетью:\n"
                "USDT TRX 1500",
                reply_markup=back_keyboard()
            )
            return

        site_name = "https://" + lines[0].strip()
        coin_lines = lines[1:]

        # ---------- ПАРСИНГ МОНЕТ ----------
        coins = []
        for line in coin_lines:
            parts = line.split()
            try:
                if len(parts) == 2:
                    symbol = parts[0].upper()
                    network = None
                    amount = float(parts[1])
                elif len(parts) >= 3:
                    symbol = parts[0].upper()
                    network = parts[1].upper()
                    amount = float(parts[2])
                else:
                    continue
            except ValueError:
                continue  # пропускаем строки где нет числа

            coins.append((symbol, network, amount))

        if not coins:
            await update.message.reply_text(
                "❗ Не удалось распознать монеты. Проверь формат.",
                reply_markup=back_keyboard()
            )
            return

        # ---------- ПОДГОТОВКА ИЗОБРАЖЕНИЯ ----------
        image = Image.open(BALANCE_TEMPLATE).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # ---------- ШРИФТЫ ----------
        font_time    = ImageFont.truetype(FONT_SF_SEMI,    size=22)
        font_site    = ImageFont.truetype(FONT_SF_REGULAR,    size=19)
        font_total   = ImageFont.truetype(FONT_SF_SEMI,    size=60)
        font_ticker  = ImageFont.truetype(FONT_SF_REGULAR,    size=24)
        font_amount  = ImageFont.truetype(FONT_SF_REGULAR,    size=24)
        font_price   = ImageFont.truetype(FONT_SF_REGULAR, size=20)

        # ---------- ВРЕМЯ ----------
        formatted_time = datetime.now().strftime("%H:%M")
        draw.text((TIME_X, TIME_Y), formatted_time, font=font_time, fill="white", anchor="lm")

        # ---------- НАЗВАНИЕ САЙТА (обрезаем если не влезает) ----------
        original_site = site_name
        while draw.textbbox((0, 0), site_name + "…", font=font_site)[2] > MAX_SITE_WIDTH:
            site_name = site_name[:-1]
        if site_name != original_site:
            site_name = site_name.rstrip() + "…"

        draw.text((SITE_X, SITE_Y), site_name, font=font_site, fill="#5f5f5f", anchor="lm")

        # ---------- КУРСЫ МОНЕТ ----------
        client = Spot()
        total_balance = 0.0

        # ---------- ОТРИСОВКА МОНЕТ ----------
        for i, (sym, network, amount) in enumerate(coins[:len(COIN_ICON_TOP_Y)]):
            icon_top = COIN_ICON_TOP_Y[i]

            # --- ИКОНКА МОНЕТЫ ---
            icon_path = f"coins/rounded_{sym}.png"
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert("RGBA")
                icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
                icon = icon.filter(ImageFilter.SMOOTH)
                image.paste(icon, (ICON_X, icon_top), icon)

            # --- ИКОНКА СЕТИ (правый нижний угол иконки монеты) ---
            if network:
                net_key = NETWORK_ICON_MAP.get(network)
                if net_key:
                    net_icon_path = f"coins/networks/{net_key}.png"
                    if os.path.exists(net_icon_path):
                        net_icon = Image.open(net_icon_path).convert("RGBA")
                        net_icon = net_icon.resize((NET_SIZE, NET_SIZE), Image.Resampling.LANCZOS)
                        net_x = ICON_X + ICON_SIZE - NET_SIZE + 2
                        net_y = icon_top + ICON_SIZE - NET_SIZE + 2
                        image.paste(net_icon, (net_x, net_y), net_icon)

            # --- ЦЕНА С BINANCE ---
            if sym == "USDT":
                price = 1.0
                change = 0.0
            else:
                try:
                    ticker_data = client.ticker_24hr(symbol=sym + "USDT")
                    price = float(ticker_data["lastPrice"])
                    change = float(ticker_data["priceChangePercent"])
                except Exception:
                    price = 0.0
                    change = 0.0

            coin_sum = price * amount
            total_balance += coin_sum

            # --- ТИКЕР (левый верхний, крупный белый) ---
            ticker_y = icon_top + TICKER_OFFSET_Y
            draw.text((TICKER_X, ticker_y), sym, font=font_ticker, fill="white", anchor="lt")

            # --- КОЛИЧЕСТВО (правый верхний, крупный белый) ---
            # Отображаем без лишних нулей: целое число если .0, иначе до 8 знаков без хвостовых нулей
            if amount == int(amount):
                amount_text = str(int(amount))
            else:
                amount_text = f"{amount:.8f}".rstrip("0").rstrip(".")
            amount_w = draw.textbbox((0, 0), amount_text, font=font_amount)[2]
            draw.text(
                (RIGHT_X - amount_w, ticker_y),
                amount_text,
                font=font_amount,
                fill="white",
                anchor="lt"
            )

            # --- ЦЕНА (левый нижний, серый) ---
            price_y = icon_top + PRICE_OFFSET_Y

            # Форматирование цены: запятая как разделитель дробной части (Bybit-стиль)
            if price >= 1:
                price_str = f"{price:,.2f}".replace(",", " ").replace(".", ",")
            else:
                # Для малых цен показываем больше знаков
                price_str = f"{price:.4f}".rstrip("0").rstrip(".").replace(".", ",")
            price_text = f"$ {price_str}"
            draw.text((TICKER_X, price_y), price_text, font=font_price, fill="#505050", anchor="lt")

            # --- ≈ СУММА USD (правый нижний, серый) ---
            if coin_sum >= 1:
                sum_str = f"{coin_sum:,.1f}".replace(",", " ").replace(".", ",")
            else:
                sum_str = f"{coin_sum:.2f}".replace(".", ",")
            sum_text = f"≈ {sum_str} USD"
            sum_w = draw.textbbox((0, 0), sum_text, font=font_price)[2]
            draw.text(
                (RIGHT_X - sum_w, price_y),
                sum_text,
                font=font_price,
                fill="#505050",
                anchor="lt"
            )

        # ---------- ОБЩИЙ БАЛАНС ----------
        if total_balance >= 1:
            total_str = f"{total_balance:,.2f}".replace(",", " ").replace(".", ",")
        else:
            total_str = f"{total_balance:.2f}".replace(".", ",")
        total_text = f"${total_str}"
        draw.text((TOTAL_X, TOTAL_Y), total_text, font=font_total, fill="white", anchor="mm")

        # ---------- СОХРАНЕНИЕ ----------
        os.makedirs(SCREENS_DIR, exist_ok=True)
        filename = os.path.join(
            SCREENS_DIR,
            f"bybit_balance_{update.message.from_user.username or 'user'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        image.save(filename, format="PNG")

        await update.message.reply_photo(
            photo=open(filename, "rb"),
            reply_markup=back_keyboard()
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠ Ошибка баланса (Bybit): {e}",
            reply_markup=back_keyboard()
        )