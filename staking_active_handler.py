import os
import re
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from keyboards import back_keyboard

# =============================
#   ДАННЫЕ ДЛЯ СТЕЙКИНГ-ЛИСТА
# =============================

STAKING_ACTIVE_TEMPLATE = "imageTemplates/trust/TemplateActiveStaking.jpg"

FONT_ROBOTO = "fonts/Roboto-Regular.ttf"
FONT_ROBOTO_SEMI = "fonts/Roboto-SemiBold.ttf"
FONT_DINPRO = "fonts/dinpro_medium.otf"
FONT_DINPRO_BOLD = "fonts/dinpro_bold.otf"
SCREENS_DIR = "screens"


FONT_SF_REGULAR = "fonts/SF-Pro-Display-Regular.otf"
FONT_SF_MEDIUM  = "fonts/SF-Pro-Display-Medium.otf"
FONT_SF_SEMI    = "fonts/SF-Pro-Display-Semibold.otf"
font_time   = ImageFont.truetype(FONT_SF_SEMI, 23)
trust_font = ImageFont.truetype(FONT_SF_MEDIUM, 23)

# =============================
#   РЕЖИМ: 📈 АКТИВНЫЙ СТЕЙКИНГ
# =============================

def generate_staking_active_card(
    site_text: str,
    title_text: str,
    staked: str,
    available: str,
    min_amount: str,
    mrp: str,
    lock_time: str,
    left_time: str,
    rewards_formatted: str,
    validator: str,
    output_path: str,
):
    img = Image.open(STAKING_ACTIVE_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)

    width, height = img.size  # например 591 x 1280

    font_small = ImageFont.truetype(FONT_ROBOTO_SEMI, 20)
    font_normal = ImageFont.truetype(FONT_ROBOTO_SEMI, 24)
    font_title = ImageFont.truetype(FONT_ROBOTO_SEMI, 28)

    # Время
    formatted_time = datetime.now().strftime("%H:%M")
    draw.text((44, 22), formatted_time, font=font_time, fill="white")

    # Сайт по центру
    site_w = draw.textlength(site_text, font=font_normal)
    draw.text(((width - site_w + 20) / 2, 86), site_text, font=font_normal, fill="white")

    # Заголовок по центру
    title_w = draw.textlength(title_text, font=font_title)
    draw.text(((width - title_w) / 2, 155), title_text, font=font_title, fill="white")

    # ПРАВАЯ колонка
    right_x = 515
    rows_y = [237, 275, 312, 349, 386, 423, 459, 497]
    values = [staked, available, staked, rewards_formatted, min_amount, mrp, lock_time, left_time]

    for value, y in zip(values, rows_y):
        text_w = draw.textlength(value, font=font_normal)
        draw.text((right_x - text_w, y), value, font=font_normal, fill="white")

    # Trust Nodes (под иконкой)
    trust_w = draw.textlength(validator, font=trust_font)
    draw.text(
        ((width - trust_w) / 2 - 142, 646),  # ← Y подбери по шаблону
        validator,
        font=trust_font,
        fill="white"
    )

    # Простейший пример "Active" / ниже — можно дополнить при желании.
    # Здесь просто сохраним изображение.

    os.makedirs(SCREENS_DIR, exist_ok=True)
    img.save(output_path, format="JPEG", quality=95)


async def handle_staking_active_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) != 9:
        await update.message.reply_text(f"❗ Ожидаю 9 строк. Сейчас пришло: {len(lines)}.",reply_markup=back_keyboard())
        return

    site_text = lines[0]
    title_text = lines[1]
    staked = lines[2]
    available = lines[3]
    min_amount = lines[4]
    mrp = lines[5]
    lock_time = lines[6]
    left_time = lines[7]
    validator = lines[8]

    # Расчёт rewards
    try:
        # Число из staked
        staked_numeric = ''.join(c for c in staked if c.isdigit() or c in '.,')
        staked_value = float(staked_numeric.replace(',', '.'))

        mrp_value = float(mrp.replace(',', '.').replace('%', ''))

        # дни из lock_time
        lock_match = re.search(r'(\d+)\s*d', lock_time.lower())
        lock_days = int(lock_match.group(1)) if lock_match else 0

        # дни из left_time
        left_match = re.search(r'(\d+)\s*d', left_time.lower())
        left_days = int(left_match.group(1)) if left_match else 0

        elapsed_days = lock_days - left_days if lock_days > 0 else 0

        total_profit = staked_value * mrp_value / 100
        rewards = (total_profit / lock_days) * elapsed_days if lock_days > 0 else 0.0

        # валюта из staked (ETH)
        currency = ''.join(c for c in staked if c.isalpha() or c.isspace()).strip()
        rewards_formatted = f"{rewards:.6f} {currency}".strip()
    except (ValueError, ZeroDivisionError) as e:
        await update.message.reply_text(f"⚠ Ошибка расчёта rewards: {e}. Проверь формат данных.", reply_markup=back_keyboard())
        return

    username = update.message.from_user.username or "user"
    ts = int(datetime.now().timestamp())
    output_path = os.path.join(SCREENS_DIR, f"stake_{username}_{ts}.jpg")

    try:
        generate_staking_active_card(
            site_text, title_text,
            staked, available,
            min_amount, mrp, lock_time, left_time,
            rewards_formatted, validator,
            output_path
        )
        with open(output_path, "rb") as f:
            await update.message.reply_photo(f, reply_markup=back_keyboard())
    except Exception as e:
        await update.message.reply_text(f"⚠ Ошибка генерации карточки: {e}", reply_markup=back_keyboard())