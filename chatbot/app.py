import asyncio
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib.dates as md
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (Message, 
                        ReplyKeyboardRemove, 
                        InlineKeyboardMarkup, 
                        InlineKeyboardButton,
                        BufferedInputFile)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
import pandas as pd
import re
from collections import Counter
import io
import json
from datetime import datetime


with open("bot_config.json", "r") as f:
    API_TOKEN = json.load(f)['token']

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


group_storage = {}
df_chat = pd.read_csv("../data/mlds_chats_msgs.csv", index_col="Unnamed: 0")
unique_chats = df_chat['chat_name'].unique().tolist()
n_chats = len(unique_chats)



async def show_main_menu(message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    groups = [f"{index + 1}. {group}" for index, group in enumerate(["Group_name_1", "Group_name_2", "Group_name_3", "Group_name_4", "Group_name_5", "Group_name_6", "Group_name_7"])]
    buttons = [InlineKeyboardButton(text=group, callback_data=f"select_group_{index + 1}") for index, group in enumerate(groups)]
    keyboard.add(*buttons)
    await message.answer("Choose a group:", reply_markup=keyboard)


# Command /start 
# --------------
# клавиатура для /start
def get_keyboard_start(chats):
    buttons = []
    for i, chat in enumerate(chats):
        buttons.append([types.InlineKeyboardButton(
            text=chat,
            callback_data=f"group_name_{i+1}")]
        )


    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message, chats):

    await message.answer(
        "Выберите, для какой группы хотите получить статистику сообщений:",
        reply_markup=get_keyboard_start(chats)
    )

# handler для кнопок /start
@dp.callback_query(F.data.in_({f"group_name_{i+1}" for i in range(n_chats)}))
async def send_random_value(callback: types.CallbackQuery, gr_storage):
    # await callback.message.answer(str(randint(1, 10)))
    group_id = int(callback.data.split("_")[-1]) - 1
    group_name = unique_chats[group_id]
    gr_storage[callback.from_user.id] = unique_chats[group_id]
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id) 
    await callback.message.answer(f"Вы выбрали группу \"{group_name}\". Для смены группы используйте команду /start", reply_markup=types.ReplyKeyboardRemove())
    # TODO: список доступных команд
    await callback.answer()
# -------------------

# Command /current_group
# -------------------
@dp.message(Command("current_group"))
async def cmd_storage(message: types.Message, gr_storage):

    user_id = message.from_user.id
    if (group_name := gr_storage.get(user_id)):
        await message.answer(f"В данный момент статистика отображается для группы \"{group_name}\". Для смены группы используйте команду /start")
    else:
        await message.answer("Группа не выбрана! Используйте /start для выбора группы")
# -----------------


# Command /top_tags
# -----------

def get_tags_df(group_name, period, df):
    if period == "top_tags_last":
        tags_df = df[df['chat_name'] == group_name]
        max_timestamp = tags_df['day_timestamp'].max()
        tags_df = tags_df[tags_df['day_timestamp'] == max_timestamp]
        tags_df = tags_df[tags_df['msg_text'].apply(lambda x: "@" in str(x))]
        if not tags_df.empty:
            return tags_df

    else: #  period == "top_tags_all"
        tags_df = df[df['chat_name'] == group_name]
        tags_df = tags_df[tags_df['msg_text'].apply(lambda x: "@" in str(x))]
        if not tags_df.empty:
           return tags_df

    return None

def get_top_tags(tags_df, top=3):
    all_tags = []
    for msg in tags_df['msg_text']:
        tags = re.findall("@[A-z0-9_]+", msg)
        all_tags.extend(tags)

    all_tags = Counter(all_tags)
    most_common = all_tags.most_common(3)
    formatted = "Топ использованных тегов:\n" + "\n".join([f"{i+1}. {tag_} - {freq} times" for i, (tag_, freq) in enumerate(most_common)])
    return formatted

def get_keyboard_top_tags():
    buttons = [
        [types.InlineKeyboardButton(
                text="За всё время",
                callback_data="top_tags_all")],
        [types.InlineKeyboardButton(
                text="За последнюю доступную дату",
                callback_data=f"top_tags_last")]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@dp.message(Command("top_tags"))
async def cmd_top_tags(message: types.Message, gr_storage):

    user_id = message.from_user.id
    if user_id in gr_storage:
        await message.answer("Выберите, за какое время вывести топ тегов:", reply_markup=get_keyboard_top_tags())
    else:
        await message.answer("Группа не выбрана! Используйте /start для выбора группы")


@dp.callback_query(F.data.startswith("top_tags_"))
async def send_random_value(callback: types.CallbackQuery, df, gr_storage):
    period = callback.data
    user_id = callback.message.chat.id
    group_name = gr_storage[user_id]

    tags_df = get_tags_df(group_name, period, df)

    if tags_df is not None:
        top_tags = get_top_tags(tags_df)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id) 
        await callback.message.answer(top_tags)
    else:
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id) 
        await callback.message.answer("Не найдено тегов за выбранный период")

    await callback.answer()

# -----------------

# Command /most_active

def get_keyboard_most_active():
    buttons = [
        [types.InlineKeyboardButton(
                text="За всё время",
                callback_data="most_active_all")],
        [types.InlineKeyboardButton(
                text="За последнюю доступную дату",
                callback_data=f"most_active_last")]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_msgs_df(group_name, period, df):
    if period == "most_active_last":
        msgs_df = df[df['chat_name'] == group_name]
        max_timestamp = msgs_df['day_timestamp'].max()
        msgs_df = msgs_df[msgs_df['day_timestamp'] == max_timestamp]
        if not msgs_df.empty:
            return msgs_df

    else: #  period == "most_active_all"
        msgs_df = df[df['chat_name'] == group_name]
        if not msgs_df.empty:
           return msgs_df

    return None

def get_most_active_users(msgs_df, n=3):
    top_messages_df = msgs_df['from_username'].value_counts().reset_index()
    n = min(n, top_messages_df.shape[0])
    tag_freqs = []
    for i in range(n):
        row = top_messages_df.iloc[i]
        tag_ = row['from_username']
        freq = row['count']
        tag_freqs.append((tag_, freq))
    formatted = "Топ наиболее активных пользователей:\n" + "\n".join([f"{i+1}. @{tag_} - {freq} times" for i, (tag_, freq) in enumerate(tag_freqs)])
    return formatted


@dp.message(Command("most_active"))
async def cmd_most_active(message: types.Message, gr_storage):

    user_id = message.from_user.id
    if user_id in gr_storage:
        await message.answer("Выберите, за какое время собрать статистику по числу отправленных сообщений:", reply_markup=get_keyboard_most_active())
    else:
        await message.answer("Группа не выбрана! Используйте /start для выбора группы")

# TODO: закинуть в вывод последней даты саму дату
@dp.callback_query(F.data.startswith("most_active_"))
async def send_random_value(callback: types.CallbackQuery, df, gr_storage):
    period = callback.data
    user_id = callback.message.chat.id
    group_name = gr_storage[user_id]

    msgs_df = get_msgs_df(group_name, period, df)

    if msgs_df is not None:
        most_active = get_most_active_users(msgs_df)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id) 
        await callback.message.answer(most_active)
    else:
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id) 
        await callback.message.answer("Не найдено тегов за выбранный период")

    await callback.answer()

# -----------------

# Command /user_dynamics *user_name*

# класс для сохранения состояния в команде /user_dynamics

def check_user_presence(user_name, group_name, df):
    usernames = set(df[df['chat_name'] == group_name]['from_username'])
    if user_name in usernames:
        return True
    else:
        return False


def get_dynamics(user_name, group_name, df):
    user_df = df[(df['chat_name'] == group_name) & (df['from_username'] == user_name)]

    dates = user_df.apply(lambda x: datetime(x.year, x.month, x.day), axis=1)
    dates_counts = dates.value_counts()
    dates_counts = dates_counts.sort_index(ascending=True)
    dates = dates_counts.index
    values = dates_counts.values

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    # specify the position of the major ticks at the beginning of the week
    ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday = 1))
    # specify the format of the labels as 'year-month-day'
    ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d'))

    plt.setp(ax.xaxis.get_majorticklabels(), rotation = 30)

    sns.lineplot(x=dates, y=values, ax=ax)
    ax.set_title(f"Динамика отправленных сообщений пользователя {user_name}", fontsize=15)
    plt.tight_layout()

    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return BufferedInputFile(buf.getvalue(), "photo.png")

class DynamicsChooser(StatesGroup):
    choosing_user = State()


@dp.message(Command("user_dynamics"))
async def cmd_user_dynamics(message: types.Message, state: FSMContext, gr_storage):

    user_id = message.from_user.id
    if user_id in gr_storage:
        await message.answer("Введите tg-ник пользователя, для которого хотите отобразить динамику активности (без @):\n"\
            "Для отмены введите /cancel"
            )
        await state.set_state(DynamicsChooser.choosing_user)
    else:
        await message.answer("Группа не выбрана! Используйте /start для выбора группы")


@dp.message(DynamicsChooser.choosing_user, F.text)
async def user_dynamics_handler(message: types.Message, state: FSMContext, gr_storage, df):
    if message.text == "/cancel":
        await message.answer("Отмена команды /user_dynamics")
        await state.clear()
    else:
        user_name = message.text
        from_user_id = message.from_user.id
        group_name = gr_storage[from_user_id]
        is_user_present = check_user_presence(user_name, group_name, df)
        if is_user_present:
            dynamics = get_dynamics(user_name, group_name, df)
            await bot.send_photo(chat_id=message.chat.id, photo=dynamics)
            await state.clear()
        else:
            await message.answer("Пользователь с таким tg-ником не найден")
            await state.clear()


# -----------------

# Command /info

@dp.message(Command("info"))
async def cmd_info(message: types.Message, df):
    last_day = df.sort_values(by='full_timestamp', ascending=False).iloc[0]
    last_day = "{}-{}-{}".format(last_day.year, last_day.month, last_day.day)

    await message.answer("Привет!\nДанный бот предназначен для считывания статистики"\
        "по сообщениям, отправленным в чатах учебных курсов программы МОВС 2023-2025\n\n"\
        f"Дата последней выгрузки чатов: {last_day}\n"\
        "Для вывода полного списка команд введите /commands"
        )
# -----------------

# Command /commands

@dp.message(Command("commands"))
async def cmd_commands(message: types.Message):
    commands_and_descr = {
    "/info": "Показать базовую информацию о боте", 
    "/commands": "Показать список команд",
    "/start": "Выбрать телеграм-чата для анализа",
    "/current_group": "Показать текущую группу",
    "/top_tags": "Показать топ-тегов в чате",
    "/most_active": "Показать наиболее активных пользователей",
    "/user_dynamics": "Показать график пользовательской активности"
    }
    formatted = "\n".join([f"{key}: {value}" for (key, value) in commands_and_descr.items()])
    await message.answer(formatted)
# -----------------



async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, df=df_chat, chats=unique_chats, gr_storage=group_storage)


if __name__ == "__main__":
    asyncio.run(main())
