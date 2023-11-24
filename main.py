#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
# import gspread_asyncio
import asyncio
from concurrent.futures import ThreadPoolExecutor
import calendar
import time
from datetime import datetime, timedelta, time
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
import os


env_path = '.env'
# Замените на свои значения

send_messages_task = None

sendTryTime = 600*4
BigTimeLimit = [23,24]
ShortTimeLimit = [3,4]
# gif = open('gif.gif', 'rb')
agree_sticker_id = "CAACAgIAAxkBAAEKzbBlX1MfZJ6Dc4vZ-FX52TdIrpqePwACCREAAoHQiUufCV73RPDwKTME"
yoga_sticker_id = 'CAACAgIAAxkBAAEKzbdlX1Oj5EEa4YoLjhs5cJr8HSs5QAACbgAD5KDOByc3KCA4N217MwQ'
yoga_sticker_id_love = 'CAACAgIAAxkBAAEKzbllX1Ragq2eswe2NT_9NrrhP-4oNwACyQEAAhZCawpNVQGnEnEQ3jME'
yoga_sticker_id_by = 'CAACAgIAAxkBAAEKzbtlX1R84xZAptpCORxVlH1d4veXmgACWg8AAsFkiUtoBn1ASv7hiDME'


# Чтение значений из файла .env и добавление их в переменные окружения
with open(env_path) as f:
    for line in f:
        key, value = line.strip().split('=', 1)
        os.environ[key] = value

group_id = os.getenv("GROUP_ID") 
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEETS_API_CREDENTIALS_JSON = os.getenv("GOOGLE_SHEETS_API_CREDENTIALS_JSON")
bot = Bot(token=TELEGRAM_BOT_TOKEN)


events_schedule = {
    "Tuesday": {
        "🕐": time(17, 30),
        "📍": "Студия Йоги ОЙЙО, ул. Хользунова, 38/7",
        "👼": "Новичковые занятия",
        "🧘🏻‍♀️": "практика медитации"
    },
    "Thursday": {
        "🕐": time(17, 00),
        "📍": "Танцевальной пространство АНДЭР, ул. Бакунина, 2А (этаж 1)",
        "👼": "Новичковые занятия",
        "🧘🏻‍♀️": "Практика медитации"
    },
    "Friday": {
        "🕐": time(19, 0),
        "📍": "Офис возле Галереи Чижова, ул. Никитинская, 42 оф. 515",
        "🐣": "Занятия для продолжающих",
        "🧘🏻‍♀️": "Практика медитации, методики очистки"
    },
    "Saturday": {
        "🕐": time(16, 0),
        "📍": "Офис, ул. 20-летия Октября, 59 оф.317",
        "👼": "16:00 - Занятия для новичков, 17:00 - занятия для продолжающих",
        "🧘🏻‍♀️": "Практика медитации"
    }

}


current_datetime = datetime.now()
day_of_week_index = current_datetime.weekday()
# day_of_week_index = 1
day_indices = [list(calendar.day_name).index(day.capitalize()) for day in events_schedule]


def find_nearest_day(current_day_index, schedule_indices):

    # Получаем индекс текущего дня недели
    current_day_index %= 7  # Если текущий индекс превышает 6, возвращаемся к началу недели
    current_date = datetime.now()

    # Устанавливаем русскую локаль
    day_names = [
        "понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье"
    ]

    # Находим ближайший день недели относительно текущего дня
    nearest_day_index = min(schedule_indices, key=lambda day_index: (day_index - current_day_index) % 7)

    # Получаем имя ближайшего дня недели 
    nearest_day_name = list(calendar.day_name)[nearest_day_index]

    # Получаем время события
    event_time = events_schedule[nearest_day_name]["🕐"]

    # Сравниваем текущее время с временем события
    if current_datetime.time() > event_time:
        # Если текущее время больше времени события, берем следующий день
        nearest_day_index = min(schedule_indices, key=lambda day_index: (day_index - (current_day_index+1)) % 7)
        # Перенаправляем день недели 
        nearest_day_name = list(calendar.day_name)[nearest_day_index]
        event_time = events_schedule[nearest_day_name]["🕐"]    

    # Calculate the difference in days to the nearest given day
    days_difference = (nearest_day_index - current_day_index + 7) % 7
    # Calculate the date of the nearest given day
    nearest_day_date = current_date + timedelta(days=days_difference)

        # Calculate the remaining time until the nearest day
    remaining_time = (datetime.combine(nearest_day_date, event_time) - datetime.now()).total_seconds()
    hours, remainder = divmod(remaining_time, 3600)
    minutes, _ = divmod(remainder, 60)

    # Format the result as hours and minutes
    remaining_time_str = f"{int(hours)} hours and {int(minutes)} minutes"

    # print('время до ближайшего мероприятия',hours)

    nearest_day_name_rus = day_names[nearest_day_index]
    formatted_string = "\n".join([f"{key}: {value}" for key, value in events_schedule[nearest_day_name].items()])

    dayEvent = {nearest_day_name_rus:formatted_string}
    dayEvent_str = "\n".join([f"{key}: {value}" for key, value in dayEvent.items()])

    return hours,minutes,nearest_day_name,dayEvent_str


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


keyboard = [
    [
        InlineKeyboardButton("Подписаться на рассылку", callback_data="yes")
    ]
]

keyboard2 = [
    [
        InlineKeyboardButton("Собираюсь пойти", callback_data="try"),
        InlineKeyboardButton("Отписаться от рассылки", callback_data="otpis"),
    ]
]

keyboard3 = [
    [
        InlineKeyboardButton("Точно пойду", callback_data="confirm"),
        InlineKeyboardButton("Не получается", callback_data="sorry"),
    ],
    [
        InlineKeyboardButton("Отписаться от рассылки", callback_data="otpis"),
    ]
]

# Define a few command handlers. These usually take the two arguments update and
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""

    user_ids,filtered_users = await get_telegram_user_ids()
    curent_user_id = update.message.chat_id  # Получаем chat_id из объекта update

    if str(curent_user_id) in user_ids:
        reply_markup = InlineKeyboardMarkup(keyboard2)
        await update.message.reply_text("Привет! Вы подписаны на Сахадж мероприятия в Воронеже, хотите отписаться?", reply_markup=reply_markup)
    else:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Привет! Хотите подписаться на Сахадж мероприятия в Воронеже?", reply_markup=reply_markup)
    

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    user_id = query.from_user.id
    user_ids,filtered_users = await get_telegram_user_ids()
    user_name = query.from_user.username
    choice = query.data


    # CallbackQueries need to be answered, even if no notification to the user is needed
    await query.answer()
    hours,minutes,eng_day,nearest_day = find_nearest_day(day_of_week_index, day_indices)
    adress_line=nearest_day.split('\n')[1]
    
    if  hours < ShortTimeLimit[1]:
        reply_markup = InlineKeyboardMarkup(keyboard3)
    if  hours > ShortTimeLimit[1]:
        reply_markup = InlineKeyboardMarkup(keyboard2)

    # Добавить пользователя в Google Таблицу
    if choice == "yes":
        if str(user_id) in user_ids:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Вы уже подписаны на мероприятия, напоминаем, ближайшее пройдет в \n 🗓 {nearest_day} через {hours} часов, {minutes} минут",reply_markup=reply_markup
            )
        else:
            await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice==False, confirmation=False ,typeOf=True)
            await update_spreadsheet_data(context.application)    
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Здорово! Ближайшее мероприятие пройдет в \n 🗓 {nearest_day} через {hours} часов, {minutes} минут" ,reply_markup=reply_markup
            )
            await context.bot.send_sticker(chat_id=user_id, sticker=agree_sticker_id )


    if choice == "otpis":
        await update_spreadsheet(user_id, user_name, GOOGLE_SHEETS_SPREADSHEET_ID, choice=False, confirmation=False, typeOf=False)
        await update_spreadsheet_data(context.application)    
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Мы вас удалили из списка рассылки. Если передумаете, нажмите на кнопку ниже", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await context.bot.send_sticker(chat_id=user_id, sticker=yoga_sticker_id_by)
    
    if choice == "try":
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=False, typeOf=False)
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=False, typeOf=True)
        await update_spreadsheet_data(context.application)    
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Здорово! Будем ждать. Ближайшее мероприятие пройдет в \n 🗓 {nearest_day} через {hours} часов, {minutes} минут. Отправим вам напоминание за 4 часа до мероприятия"
        )
        await send_notifications_to_group_try(user_name)
        await context.bot.send_sticker(chat_id=user_id, sticker=yoga_sticker_id_love)
    
    if choice == "confirm":

        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=False, typeOf=False)
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=True, typeOf=True)
        await update_spreadsheet_data(context.application)    
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Ваша Кундалини поднимается, мы Вас ждем через {hours} часов, {minutes} минут по адресу {adress_line}!",
        )

        await send_notifications_to_group_confirm(user_name)
        await context.bot.send_sticker(chat_id=user_id, sticker=yoga_sticker_id)

    if choice == "sorry":
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=False, typeOf=False)
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=False, confirmation=False, typeOf=True)
        await update_spreadsheet_data(context.application)    
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Ничего страшного, приходите на следующее занятие, мы Вас оповестим о нем заранее!"
        )
        await send_notifications_to_group_sorry(user_name)



async def send_notifications_to_group_try(user_name):
    hours,minutes,eng_day,nearest_day = find_nearest_day(day_of_week_index, day_indices)
    text_line=nearest_day.split('\n')[0]
    await bot.send_message(group_id, f"\n На {text_line} \n есть пердварительная запись от {user_name}")

async def send_notifications_to_group_confirm(user_name):
    hours,minutes,eng_day,nearest_day = find_nearest_day(day_of_week_index, day_indices)
    text_line=nearest_day.split('\n')[0]
    await bot.send_message(group_id, f"\n На {text_line} \n есть подтвержденная запись от {user_name}")

async def send_notifications_to_group_sorry(user_name):
    hours,minutes,eng_day,nearest_day = find_nearest_day(day_of_week_index, day_indices)
    text_line=nearest_day.split('\n')[0]
    await bot.send_message(group_id, f"\n На {text_line} \n {user_name} не сможет придти")


async def update_spreadsheet_data(application):
    # global send_messages_task
    await get_telegram_user_ids()


# Добавляем тех пользователей которые согласились в таблицу
async def update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice, confirmation, typeOf):
    # Аутентификация в Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_API_CREDENTIALS_JSON, scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)

    # Получение активного листа (первого листа в таблице)
    sheet = spreadsheet.get_worksheet(0)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Выбираем лист таблицы
    row_data = [user_id, user_name, choice, confirmation, timestamp]

    # Добавляем данные
    if typeOf:
        sheet.append_row(row_data)
    else:
        cell = sheet.find(str(user_id))
        sheet.delete_row(cell.row)




# Получаем согласившихся пользователей из таблицы
async def get_telegram_user_ids():
    # Загрузка учетных данных

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_API_CREDENTIALS_JSON, scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)

    # Аутентификация и открытие таблицы по идентификатору
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)

    # Получение активного листа (первого листа в таблице)
    sheet = spreadsheet.get_worksheet(0)

    # Получение списка ID пользователей
    user_ids = await asyncio.to_thread(sheet.col_values, 1)
    user_agrees = await asyncio.to_thread(sheet.col_values, 3)

    # Фильтрация пользователей, оставляем только тех, у кого 3-ий столбец равен True
    filtered_users = [user_id for user_id, agrees in zip(user_ids, user_agrees) if agrees.lower() == 'true']

    print("получаем всех пользователей из таблицы" ,user_ids)
    print("получаем всех пользователей, кто собирается придти", filtered_users)
    return user_ids,filtered_users


async def send_messages_to_users():
    hours, minutes, eng_day, nearest_day = find_nearest_day(day_of_week_index, day_indices)
    reply_markup = InlineKeyboardMarkup(keyboard2)
    print('ближайшее мероприятие-',eng_day)
    print('время до ближайшего мероприятия для собирающихся-',hours)

    try:
        # Check if the message has already been sent
        if BigTimeLimit[0] <= hours < BigTimeLimit[1]:
            user_ids,filtered_users = await get_telegram_user_ids()
            print('пользователи, кому отправляются сообщения',user_ids)
            for user_id in user_ids:
                # Send the reminder message
                await bot.send_message(user_id, f"\n Напоминание на {nearest_day}. \n Мероприятие начнется через {hours} часов и {minutes} минут", reply_markup=reply_markup)
                print(f"Напоминание отправлено пользователю {user_id}")
    except Exception as e:
        print(f"Произошла ошибка при отправке сообщения: {e}")



async def send_reminder_to_users():
    hours, minutes, eng_day, nearest_day = find_nearest_day(day_of_week_index, day_indices)
    reply_markup = InlineKeyboardMarkup(keyboard3)
    print('ближайшее мероприятие для собирающихся-',eng_day)
    print('время до ближайшего мероприятия для уверенных-',hours)

    try:
         if ShortTimeLimit[0] <= hours < ShortTimeLimit[1]:
            user_ids,filtered_users = await get_telegram_user_ids()
            print('пользователи, кому отправляются сообщения',user_ids)
            for user_id in user_ids:
                # Send the reminder message
                await bot.send_message(user_id, f"\n Напоминание на {nearest_day}. \n Мероприятие начнется через {hours} часов и {minutes} минут", reply_markup=reply_markup)
                print(f"Напоминание отправлено пользователю {user_id}")
    except Exception as e:
        print(f"Произошла ошибка при отправке сообщения: {e}")



async def cleanup(application, send_messages_task):
    application.stop()
    send_messages_task.cancel()
    await asyncio.gather(
        application.run_until_complete(application.shutdown()),
        send_messages_task
    )

async def main_task():
    while True:
        # Запуск асинхронных функций с использованием asyncio.ensure_future
        asyncio.ensure_future(send_messages_to_users())
        asyncio.ensure_future(send_reminder_to_users())
        await asyncio.sleep(sendTryTime)


def main() -> None:
    # global send_messages_task
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Запускаем задачу main_task через заданный интервал времени
    main_task_task = loop.create_task(main_task())

    try:
        # Запускаем бота в созданном цикле
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        # Если пользователь прерывает выполнение программы, выполняем очистку
        loop.run_until_complete(cleanup(application, main_task_task))


if __name__ == "__main__":
    main()