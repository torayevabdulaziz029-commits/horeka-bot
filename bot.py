import os
import pandas as pd
import folium
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton

# ⚠️ O'z bot tokeningizni shu yerga yozing
TOKEN = "9205527655:AAGZjyDSpxQH8D3bN_wyUYghnoDr8iMKEeY"

# 🟢 MAXFIYLIK UCHUN: Ruxsat berilgan foydalanuvchilarning Telegram ID raqamlari
# (123456789 o'rniga O'Z ID RAQAMINGIZNI yozing)
ALLOWED_USERS = [8247658866]  

bot = Bot(token=TOKEN)
dp = Dispatcher()

def categorize(name):
    name_lower = str(name).lower()
    if any(w in name_lower for w in ['гостиница', 'отель', 'plaza', 'плаза', 'hotel']):
        return 'Mehmonxona'
    elif any(w in name_lower for w in ['кидс', 'школа', 'лицей', 'сад', 'бохча', 'нтм', 'университет', 'детский', 'мактаб', 'боғча']):
        return 'Maktab / Bog\'cha'
    elif any(w in name_lower for w in ['фитнес', 'спорт', 'gym', 'fitness']):
        return 'Fitnes / Sport'
    elif any(w in name_lower for w in ['кафе', 'ресторан', 'ошхона', 'суши', 'кофе', 'coffee', 'cafe', 'restaurant', 'fast', 'лаззат', 'папаха', 'бургер', 'бар']):
        return 'Restoran / Kafe'
    else:
        return None

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    # 🔒 ID tekshiruvi (Maxfiylik uchun)
    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("❌ Kechirasiz, bu yopiq (maxfiy) korporativ bot. Sizda bu botdan foydalanish huquqi yo'q.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗺 Toshkent xaritasini olish")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Salom! Xaritani olish uchun quyidagi tugmani bosing:", 
        reply_markup=kb
    )

@dp.message(lambda msg: msg.text in ["🗺 Toshkent xaritasini olish", "/map"])
async def generate_map(message: types.Message):
    # 🔒 ID tekshiruvi
    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("❌ Kechirasiz, sizga ruxsat berilmagan.")
        return

    await message.answer("🔍 Xarita tayyorlanmoqda...")
    
    try:
        excel_file = "Horeka.xlsx"
        if not os.path.exists(excel_file):
            await message.answer("❌ 'Horeka.xlsx' fayli topilmadi!")
            return

        df = pd.read_excel(excel_file, header=2)
        
        name_col = df.columns[1]
        status_col = df.columns[2]
        lat_col = df.columns[6]
        lon_col = df.columns[7]

        df = df.dropna(subset=[lat_col, lon_col])

        m = folium.Map(
            location=[41.2995, 69.2401], 
            zoom_start=12,
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            attr="Esri"
        )

        active_count = 0
        potential_count = 0

        for _, row in df.iterrows():
            try:
                name = str(row[name_col]).strip()
                status = str(row[status_col]).strip()
                lat = float(str(row[lat_col]).replace(',', '.'))
                lon = float(str(row[lon_col]).replace(',', '.'))
            except:
                continue

            cat = categorize(name)
            if not cat:
                continue

            if status == "Активный":
                color = 'green'
                status_text = "Biz bilan ishlaydi (Aktiv)"
                active_count += 1
            else:
                color = 'red'
                status_text = "Biz bilan ishlamaydi"
                potential_count += 1

            popup_text = f"<b>{name}</b><br>Turi: {cat}<br>Holati: {status_text}"
            
            folium.Marker(
                location=[lat, lon],
                popup=popup_text,
                icon=folium.Icon(color=color, icon='info-sign', prefix='fa')
            ).add_to(m)

        map_path = "map.html"
        m.save(map_path)

        caption = (
            f"✅ **Xarita tayyor!**\n\n"
            f"🟢 **Aktiv mijozlar:** {active_count} ta\n"
            f"🔴 **Ishlamaydiganlar:** {potential_count} ta\n\n"
            f"📺 *Barcha nuqtalar alohida va toza ko'rinishda chiqarildi.*"
        )

        document = FSInputFile(map_path)
        await message.answer_document(document, caption=caption, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))