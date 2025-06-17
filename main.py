import json, asyncio
from aiogram import F, Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (Message, CallbackQuery, KeyboardButton,
                           ReplyKeyboardMarkup, InlineKeyboardButton,
                           InlineKeyboardMarkup)
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8052308820:AAHtNTjNFz05wF4v5r0G74vZT5ZNa-ssD1o"
ADMIN_ID = 6560139113

DATA_FILE = 'data.json'
USERS_FILE = 'users.json'
CHANNELS_FILE = 'channels.json'

bot = Bot(token=BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


class ChannelState(StatesGroup):
    add = State()
    remove = State()


class AddCourseState(StatesGroup):
    category = State()
    company = State()
    lesson = State()
    video = State()


def load_json(path, default):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_data():
    return load_json(DATA_FILE, {})


def save_data(x):
    save_json(DATA_FILE, x)


def load_users():
    return load_json(USERS_FILE, [])


def save_users(x):
    save_json(USERS_FILE, x)


def load_channels():
    return load_json(CHANNELS_FILE, [])


def save_channels(x):
    save_json(CHANNELS_FILE, x)


async def is_user_subscribed(uid: int) -> bool:
    for ch in load_channels():
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=uid)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True


def track_user(uid: int):
    users = load_users()
    if uid not in users:
        users.append(uid)
        save_users(users)


def build_main_menu():
    data = load_data()
    keyboard = [[KeyboardButton(text=cat)] for cat in data.keys()]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_admin_panel_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
        [
            InlineKeyboardButton(text="➕ Kanal qo‘shish",
                                 callback_data="add_channel")
        ],
        [
            InlineKeyboardButton(text="➖ Kanal o‘chirish",
                                 callback_data="del_channel")
        ],
        [
            InlineKeyboardButton(text="➕ Kategoriya qo‘shish",
                                 callback_data="add_category")
        ],
    ])


def back_to_panel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_panel")
    ]])
    return keyboard


def build_company_menu(cat: str):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=comp)]
                                         for comp in load_data()[cat].keys()] +
                               [[KeyboardButton(text="⬅️ Orqaga")]],
                               resize_keyboard=True)


def build_lesson_menu(cat: str, comp: str):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=les)]
                  for les in load_data()[cat][comp].keys()] +
        [[KeyboardButton(text="⬅️ Orqaga")]],
        resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(msg: Message):
    uid = msg.from_user.id
    if await is_user_subscribed(uid):
        track_user(uid)
        await msg.answer("<b>📂 Asosiy menyu:</b>",
                         reply_markup=build_main_menu())
    else:
        channels = load_channels()
        btns = [[InlineKeyboardButton(text=ch, url=f"https://t.me/{ch[1:]}")]
                for ch in channels]
        btns.append([
            InlineKeyboardButton(text="✅ Tekshirish",
                                 callback_data="check_sub")
        ])
        await msg.answer(
            "<b><b>Quyidagi kanallarga obuna bo‘ling</b></b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))


@dp.callback_query(lambda c: c.data == "check_sub")
async def on_check(call: CallbackQuery):
    uid = call.from_user.id
    if await is_user_subscribed(uid):
        track_user(uid)
        await call.message.edit_text("<b>✅ Obuna tasdiqlandi.</b>")
        user_name = call.from_user.first_name
        await bot.send_message(uid,
                               f"""<b>👋 Assalomu alaykum {user_name}!

✅ Ushbu bot orqali siz turli sohalardagi video darslarni qulay tarzda tomosha qilishingiz mumkin.

📂 Mavzular bo‘yicha darslarni ko‘rish uchun oddiygina menyudan kerakli darslarni tanlang!

🎓 Har bir sohalar ichida siz uchun alohida darslar joylashtirilgan — barchasi sizning rivojlanishingiz uchun!</b>""",
                               reply_markup=build_main_menu(),
                               parse_mode="HTML")
    else:
        await call.answer("❌ Hali ham obuna bo‘lmadingiz!", show_alert=True)


@dp.message(Command("panel"))
async def cmd_panel(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer(
        "<b>Assalomu Aleykum Admin panelida Foydalanishingiz mumkin!</b>",
        reply_markup=get_admin_panel_markup())


@dp.callback_query(lambda c: c.data == "stats")
async def cb_stats(call: CallbackQuery):
    category_count = len(load_data())
    company_count = sum(len(companies) for companies in load_data().values())
    lesson_count = sum(
        len(company) for category in load_data().values()
        for company in category.values())

    await call.message.edit_text(
        f"<b>👥 Foydalanuvchilar soni:</b> {len(load_users())}\n"
        f"<b>📢 Kanallar soni:</b> {len(load_channels())}\n"
        f"<b>📁 Kategoriyalar soni:</b> {category_count}\n"
        f"<b>🏢 Kompaniyalar soni:</b> {company_count}\n"
        f"<b>🎬 Darslar soni:</b> {lesson_count}",
        reply_markup=back_to_panel_keyboard(),
        parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "back_to_panel")
async def back_to_panel(call: CallbackQuery):
    await call.message.edit_text("<b>🔧 Admin paneliga qaytdingiz.</b>",
                                 reply_markup=get_admin_panel_markup())


@dp.callback_query(lambda c: c.data == "add_channel")
async def cb_add_ch(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "<b>➕ Kanalingizni kiriting:</b>\n\n<b>Misol uchun <code>@username</code> deb yozing!</b>",
        reply_markup=back_to_panel_keyboard())
    await state.set_state(ChannelState.add)


@dp.message(StateFilter(ChannelState.add))
async def msg_add_ch(msg: Message, state: FSMContext):
    ch = msg.text.strip()
    chs = load_channels()
    if ch.startswith("@") and ch not in chs:
        chs.append(ch)
        save_channels(chs)
        await msg.answer("<b>✅ Kanal qo‘shildi.</b>")
    else:
        await msg.answer("<b>❗ Format noto‘g‘ri yoki mavjud.</b>")
    await state.clear()


@dp.callback_query(lambda c: c.data == "del_channel")
async def cb_del_ch(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "<b>➖ Kanal o‘chirish uchun @username kiriting:</b>\n\n<b>Misol uchun <code>@username</code> deb yozing!</b>",
        reply_markup=back_to_panel_keyboard())
    await state.set_state(ChannelState.remove)


@dp.message(StateFilter(ChannelState.remove))
async def msg_remove_ch(msg: Message, state: FSMContext):
    ch = msg.text.strip()
    chs = load_channels()
    if ch in chs:
        chs.remove(ch)
        save_channels(chs)
        await msg.answer("<b>✅ Kanal o‘chirildi.</b>")
    else:
        await msg.answer("<b>❗ Kanal topilmadi.</b>")
    await state.clear()


@dp.callback_query(F.data == "add_category")
async def cb_add_cat(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("<b>➕ Kategoriya nomini yozing:</b>",
                                 reply_markup=back_to_panel_keyboard())
    await state.set_state(AddCourseState.category)
    reply_markup = back_to_panel_keyboard(),


@dp.message(StateFilter(AddCourseState.category))
async def msg_add_cat(msg: Message, state: FSMContext):
    cat = msg.text.strip()
    d = load_data()
    if cat not in d:
        d[cat] = {}
        save_data(d)
        await msg.answer("<b>✅ Kategoriya qo‘shildi.</b>")
    else:
        await msg.answer("<b>❗ Kategoriya mavjud.</b>")
    await state.update_data(category=cat)
    await state.set_state(AddCourseState.company)
    await msg.answer("<b>📩 Kompaniya nomini yozing:</b>")


@dp.message(StateFilter(AddCourseState.company))
async def msg_add_comp(msg: Message, state: FSMContext):
    comp = msg.text.strip()
    u = await state.get_data()
    d = load_data()
    if comp not in d[u["category"]]:
        d[u["category"]][comp] = {}
        save_data(d)
        await msg.answer("<b>✅ Kompaniya qo‘shildi.</b>")
    else:
        await msg.answer("<b>❗ Kompaniya allaqachon mavjud.</b>")
    await state.update_data(company=comp)
    await state.set_state(AddCourseState.lesson)
    await msg.answer("<b>📌 Dars nomini kiriting:</b>")


@dp.message(StateFilter(AddCourseState.lesson))
async def msg_add_less(msg: Message, state: FSMContext):
    await state.update_data(lesson=msg.text.strip())
    await msg.answer("<b>📹 Dars videosi post havolasini yuboring:</b>")
    await state.set_state(AddCourseState.video)


@dp.message(StateFilter(AddCourseState.video))
async def msg_add_video(msg: Message, state: FSMContext):
    url = msg.text.strip()

    if not url.startswith("https://t.me/"):
        return await msg.answer(
            "<b>❗ To‘g‘ri Telegram post havolasini yuboring.</b>")

    try:
        parts = url.replace("https://t.me/", "").split("/")
        username = parts[0]
        message_id = int(parts[1])

        chat = await bot.get_chat(f"@{username}")
        chat_id = chat.id

        u = await state.get_data()
        d = load_data()
        d[u["category"]][u["company"]][u["lesson"]] = {
            "chat_id": chat_id,
            "message_id": message_id
        }
        save_data(d)
        await msg.answer("<b>✅ Dars saqlandi.</b>")
        await state.clear()

    except Exception as e:
        await msg.answer(f"<b>❗ Xatolik yuz berdi: {e}</b>")


@dp.message()
async def navigation(msg: Message):
    uid = msg.from_user.id
    if not await is_user_subscribed(uid):
        return await msg.answer(
            "<b>❗ Avval kanallarga obuna bo‘ling</b> - /start")
    txt = msg.text.strip()
    d = load_data()
    if txt == "⬅️ Orqaga":
        return await msg.answer("<b>📂 Asosiy menyu:</b>",
                                reply_markup=build_main_menu())
    if txt in d:
        return await msg.answer("<b>📁 Kompaniyani tanlang:</b>",
                                reply_markup=build_company_menu(txt))
    for cat in d:
        if txt in d[cat]:
            return await msg.answer("<b>🎬 Darsni tanlang:</b>",
                                    reply_markup=build_lesson_menu(cat, txt))
        for comp in d[cat]:
            if txt in d[cat][comp]:
                i = d[cat][comp][txt]
                return await bot.copy_message(chat_id=msg.chat.id,
                                              from_chat_id=i["chat_id"],
                                              message_id=i["message_id"])


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
