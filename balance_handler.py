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

BALANCE_TEMPLATE = "imageTemplates/trust/TemplateBalance.jpg"
SCREENS_DIR = "screens"

FONT_DINPRO = "fonts/dinpro_medium.otf"
FONT_DINPRO_BOLD = "fonts/dinpro_bold.otf"
FONT_ROBOTO_SEMI = "fonts/Roboto-SemiBold.ttf"
FONT_SF_REGULAR = "fonts/SF-Pro-Display-Regular.otf"
FONT_SF_SEMI = "fonts/SF-Pro-Display-Semibold.otf"
FONT_SF_BOLD = "fonts/SF-Pro-Display-Bold.otf"
FONT_SF_MEDIUM = "fonts/SF-Pro-Display-Medium.otf"

IMAGE_WIDTH = 591
IMAGE_HEIGHT = 1280

# Y-координаты строк монет (до 6 штук)
percent_y_balance = (520, 615, 710, 805, 900, 995)

SITE_TEXT_X = 220  # отступ вправо от иконки X/замка
SITE_TEXT_Y = 100
MAX_SITE_WIDTH = IMAGE_WIDTH - SITE_TEXT_X - 20


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
#      РЕЖИМ: БАЛАНС
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
                "ETH 2",
                reply_markup=back_keyboard()
            )
            return

        site_name = lines[0].strip()
        coin_lines = lines[1:]

        # защита от слишком длинного текста
        if len(site_name) > 32:
            site_name = site_name[:29] + "..."

        # ---------- ПОДГОТОВКА ИЗОБРАЖЕНИЯ ----------
        image = Image.open(BALANCE_TEMPLATE).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # ---------- ШРИФТЫ ----------
        font_site = ImageFont.truetype(FONT_SF_SEMI, size=24)
        font_total = ImageFont.truetype(FONT_SF_SEMI, size=45)
        font_coin = ImageFont.truetype(FONT_SF_MEDIUM, size=22)
        font_coin_bold = ImageFont.truetype(FONT_DINPRO_BOLD, size=24)
        font_small = ImageFont.truetype(FONT_SF_REGULAR, size=17)
        font_price = ImageFont.truetype(FONT_SF_REGULAR, size=18)
        font_time = ImageFont.truetype(FONT_SF_SEMI, size=23)
        font_ticker = ImageFont.truetype(FONT_SF_SEMI, size=22)  # тикер (ALGO)
        font_name_pill = ImageFont.truetype(FONT_SF_MEDIUM, size=18)  # имя в плашке
        font_amount = ImageFont.truetype(FONT_SF_SEMI, size=22)

        # ---------- ВРЕМЯ ----------
        formatted_time = datetime.now().strftime("%H:%M")
        draw.text((44, 22), formatted_time, font=font_time, fill="white")


        # ---------- НАЗВАНИЕ САЙТА ----------
        original_site = site_name

        # режем так, чтобы ВЛЕЗАЛО вместе с "…"
        while draw.textbbox((0, 0), site_name + "…", font=font_site)[2] > MAX_SITE_WIDTH:
            site_name = site_name[:-1]

        # если резали — добавляем многоточие
        if site_name != original_site:
            site_name = site_name.rstrip() + "…"

        draw.text(
            (SITE_TEXT_X, SITE_TEXT_Y),
            site_name,
            font=font_site,
            fill="white",
            anchor="lm"
        )

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
                continue

            coins.append((symbol, network, amount))

        client = Spot()
        total_balance = 0.0


        # ---------- ОТРИСОВКА МОНЕТ ----------
        for i, (sym, network, amount) in enumerate(coins[:len(percent_y_balance)]):
            y = percent_y_balance[i]

            # --- ИКОНКА ---
            icon_path = f"coins/rounded_{sym}.png"
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert("RGBA")
                icon = icon.resize((57, 57), Image.Resampling.LANCZOS)
                icon = icon.filter(ImageFilter.SMOOTH)
                image.paste(icon, (23, y), icon)

            # --- ИКОНКА СЕТИ (правый нижний угол) ---
            if network:
                net_key = NETWORK_ICON_MAP.get(network)
                if net_key:
                    net_icon_path = f"coins/networks/{net_key}.png"

                    if os.path.exists(net_icon_path):
                        net_icon = Image.open(net_icon_path).convert("RGBA")

                        NET_SIZE = 22  # идеальный размер под iOS
                        net_icon = net_icon.resize((NET_SIZE, NET_SIZE), Image.Resampling.LANCZOS)

                        # позиция: правый нижний угол иконки монеты
                        net_x = 23 + 57 - NET_SIZE + 2
                        net_y = y + 57 - NET_SIZE + 2

                        image.paste(net_icon, (net_x, net_y), net_icon)

            # --- ТИКЕР (как в оригинале) ---
            ticker_x = 104
            ticker_y = y - 4
            draw.text((ticker_x, ticker_y), sym, font=font_ticker, fill="white")

            ticker_w = draw.textbbox((0, 0), sym, font=font_ticker)[2]

            # --- ПОЛНОЕ ИМЯ В ОВАЛЬНОЙ ПЛАШКЕ ---
            full_name = crypto_dict.get(sym, sym)

            pill_padding_x = 10
            pill_h = 26
            pill_radius = 13

            pill_x = ticker_x + ticker_w + 14
            pill_y = y - 5  # чуть выше, чтобы совпасть с оригиналом

            name_box = draw.textbbox((0, 0), full_name, font=font_name_pill)
            name_w = name_box[2] - name_box[0]

            # сама плашка
            draw.rounded_rectangle(
                [pill_x, pill_y, pill_x + name_w + pill_padding_x * 2, pill_y + pill_h],
                radius=pill_radius,
                fill="#2b2b2b"  # серый фон как в оригинале
            )

            # текст внутри плашки
            draw.text(
                (pill_x + pill_padding_x, pill_y + 2),
                full_name,
                font=font_name_pill,
                fill="white"
            )

            # --- ЦЕНА ---
            if sym == "USDT":
                price = 1.0
                change = 0.0
            else:
                ticker = client.ticker_24hr(symbol=sym + "USDT")
                price = float(ticker["lastPrice"])
                change = float(ticker["priceChangePercent"])

            price_text = f"{price:,.2f}".replace(",", " ").replace(".", ",") + " $"
            draw.text((104, y + 30), price_text, font=font_price, fill="#9d9d9d")

            change_color = "#9d9d9d"
            if change > 0:
                change_color = "#529176"
            elif change < 0:
                change_color = "#e4566c"

            if change != 0:
                change_text = f"{change:.2f}".replace(".", ",") + "%"
                price_width = draw.textbbox((0, 0), price_text, font=font_price)[2]
                draw.text(
                    (104 + price_width + 7, y + 30),
                    change_text,
                    font=font_price,
                    fill=change_color
                )

            # --- КОЛ-ВО СПРАВА ---
            right_x = IMAGE_WIDTH - 30
            amount_text = f"{amount:.2f}"
            amount_width = draw.textbbox((0, 0), amount_text, font=font_amount)[2]
            draw.text(
                (right_x - amount_width, y - 3),
                amount_text,
                font=font_amount,
                fill="white"
            )

            # --- СУММА ---
            coin_sum = price * amount
            total_balance += coin_sum

            sum_text = f"{coin_sum:.2f}".replace(".", ",") + " $"
            sum_width = draw.textbbox((0, 0), sum_text, font=font_price)[2]
            draw.text(
                (right_x - sum_width, y + 30),
                sum_text,
                font=font_price,
                fill="#9d9d9d"
            )

        # ---------- ОБЩИЙ БАЛАНС ----------
        total_text = f"{total_balance:,.2f}".replace(",", " ").replace(".", ",") + " $"
        draw.text(
            (IMAGE_WIDTH // 2, 230),
            total_text,
            font=font_total,
            fill="white",
            anchor="mm"
        )


        # ---------- СОХРАНЕНИЕ ----------
        os.makedirs(SCREENS_DIR, exist_ok=True)
        filename = os.path.join(
            SCREENS_DIR,
            f"balance_{update.message.from_user.username or 'user'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        )
        image.save(filename, format="PNG")


        await update.message.reply_photo(
            photo=open(filename, "rb"),
            reply_markup=back_keyboard()
        )


    except Exception as e:

        import traceback

        await update.message.reply_text(

            f"⚠ Ошибка баланса: {e}\n\n{traceback.format_exc()}",

            reply_markup=back_keyboard()

        )
