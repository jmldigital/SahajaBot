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
import json


env_path = '.env'
# Замените на свои значения

send_messages_task = None

sendTryTime = 600*6
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
        "Занятие для новичков": {
        "🕐": time(17, 30),
        "📍": "Студия Йоги ОЙЙО, ул. Хользунова, 38/7\n https://yandex.ru/maps/-/CDe-bHYN",
        "🧘🏻‍♀️": "Практика медитации"
        }
    },

    "Thursday": {
        "Занятие для новичков": {
        "🕐": time(17, 00),
        "📍": "Танцевальное пространство АНДЭР, ул. Бакунина, 2А, 2-й этаж \n https://yandex.ru/maps/-/CDe-bL~J",
        "🧘🏻‍♀️": "Практика медитации"
        }
    },

    "Friday": {
        "Занятие для продолжающих": {
        "🕐": time(19, 0),
        "📍": "Офис возле Галереи Чижова, ул. Никитинская, 42, 5-й этаж оф. 515 \n https://yandex.ru/maps/-/CDe-bTjS",
        "🧘🏻‍♀️": "Практика медитации, методики очистки",
        }
    },

    "Saturday": {
        "Занятие для новичков": {
        "🕐": time(16, 00),
        "📍": "Офис, ул. 20-летия Октября, 59 оф.317, 3-й этаж \n https://yandex.ru/maps/-/CDe-b2ij",
        "🧘🏻‍♀️": "Практика медитации"
        },
        "Занятие для продолжающих": {
        "🕐": time(17, 00),
        "📍": "Офис, ул. 20-летия Октября, 59 оф.317, 3-й этаж \n https://yandex.ru/maps/-/CDe-b2ij",
        "🧘🏻‍♀️": "Практика медитации, методики очистки",
        }

    }

}


def filter_calendar(calendar, filter_strings):

    filter_strings_list = filter_strings.split(';')
    filter_strings_list = [item for item in filter_strings_list if item.strip()]
    # print('filter_strings_list',filter_strings_list)
    filtered_events = {}

    for filter_string in filter_strings_list:
        day, event_name = filter_string.split(":")

        # Проверка существования дня и мероприятия в календаре
        if day in calendar and event_name in calendar[day]:
            # Добавление события в отфильтрованный календарь
            filtered_events.setdefault(day, {})[event_name] = calendar[day][event_name]

    return filtered_events


def translate_days_to_russian(english_day):
    days_translation = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }

    return days_translation.get(english_day, english_day)


def get_day_index(day_name):
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    try:
        day_index = days_of_week.index(day_name)
        return day_index
    except ValueError:
        print(f"Ошибка: {day_name} не является днём недели.")
        return None



async def time_until_event():
    # Получение текущего времени
    current_time = datetime.now()
    # day_of_week_index = current_time.weekday()
    # Рассчет времени до каждого мероприятия
    for day, events in events_schedule.items():
        for event_name, event_info in events.items():
            event_time = event_info.get("🕐")
            event_geo = "📍 "+ event_info.get("📍")
            event_opis = "🧘🏻‍♀️ "+ event_info.get("🧘🏻‍♀️")
            event_day = "🗓 " + translate_days_to_russian(day) + " 🕐"+ str(event_time)
            event_title ="🚀 "+ event_name
            event_shelude = day + ":"+ event_name
            event_text=event_day + '\n'+ event_title + '\n' + event_geo + '\n' + event_opis

            # Время мероприятия
            event_datetime = datetime.combine((current_time + timedelta(days=(get_day_index(day) - current_time.weekday() + 7) % 7)).date(), event_time)
            # print('время мероприятия',type(event_datetime))
            # Рассчет разницы во времени
            time_difference = (event_datetime - current_time).total_seconds() / 3600
            # print('сейчас-',current_time, '-time_difference',time_difference )
            # print('событие\n',day,'\n',event_name,'\n',event_info)


            if time_difference //1 == BigTimeLimit[1]:
                await send_messages_to_users(event_text,event_shelude)
            if time_difference //1 == ShortTimeLimit[1]:
                await send_reminder_to_users(event_text)

    # print('ближайшая дельта',nearest_time_delta,'ближайший день',near_day,'ближайшее занятие',near_title)
    return event_day



# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



keyboard_start = [
[
        InlineKeyboardButton("🗓 Расписание занятий", callback_data="shelude")
    ]
]

keyboard_start_old = [

        [
        InlineKeyboardButton("⭐️ Мое расписание", callback_data="my_shelude"),
        InlineKeyboardButton("🗓 Общее расписание", callback_data="shelude")
         ]

]

keyboard22 = [
    [
        InlineKeyboardButton("Собираюсь на занятие", callback_data="try")

    ],
        keyboard_start_old[0]
]

keyboard3 = [
    [
        InlineKeyboardButton("Точно пойду", callback_data="confirm"),
        InlineKeyboardButton("Не получается", callback_data="sorry"),
    ],
        keyboard_start_old[0]
]


# Define a few command handlers. These usually take the two arguments update and
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""

    user_ids,filtered_users = await get_telegram_user_ids()
    curent_user_id = update.message.chat_id  # Получаем chat_id из объекта update
    user_name = update.message.from_user.username

    if str(curent_user_id) in user_ids:
        reply_markup = InlineKeyboardMarkup(keyboard_start_old)
        await update.message.reply_text(f'Привет! {user_name} Пусть Ваше внимание всегда будет высоко!', reply_markup=reply_markup)
    else:
        reply_markup = InlineKeyboardMarkup(keyboard_start)
        await update.message.reply_text('''Привет! мы Сахаджа Йоги города Воронеж сделали этого бота, чтобы напомнить всем желающим где и когда проходят регулярные бесплатные занятия по Сахадж-медитации. 

Вы можете подписаться на рассылку на удобные для вас дни недели для посещения 👇, и бот будет присылать вам уведомления за 24 часа до начала занятий в выбранные дни, чтобы вы ничего не пропустили.''', reply_markup=reply_markup)



def format_events_schedule(events_schedule,Subscribe=True):
    messages_with_keyboard = []

    for day, events in events_schedule.items():
        for event_name, event_details in events.items():
            message = f"{translate_days_to_russian(day)} - {event_name}:\n"

            # Ширина первого столбца
            column_width = 0

            for key, value in event_details.items():
                if isinstance(value, time):
                    formatted_time = value.strftime("%H:%M")
                    message += f"{key.ljust(column_width)}: {formatted_time}\n"
                else:
                    message += f"{key.ljust(column_width)}: {value}\n"

            # Создаем кнопку для текущего события
            if Subscribe==True:
                button_text = "Подписаться на " + translate_days_to_russian(day) + '🔔'
                buttons = [InlineKeyboardButton(button_text, callback_data=f"{day+event_name}")]
                keyboard = [buttons]
            else:
                button_text = "Отписаться от " + translate_days_to_russian(day) + ' 🔕'
                button_row1 = [InlineKeyboardButton(button_text, callback_data=f"otpis_{day+event_name}")]
                button_row2 = keyboard_start_old[0]
                buttons = [button_row1,button_row2]
                keyboard = buttons

            
            

            messages_with_keyboard.append((message, InlineKeyboardMarkup(keyboard)))

    return messages_with_keyboard


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_shelude={}
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    user_id = query.from_user.id
    # user_ids,users_shelude_strings = await get_telegram_user_ids()
    user_name = query.from_user.username
    choice = query.data
    # CallbackQueries need to be answered, even if no notification to the user is needed
    await query.answer()

    #Подписка пользователя
    for day, events in events_schedule.items():
        for event_name,event_details in events.items():
            if choice == f"{day+event_name}":
                # user_shelude[day] = event_name
                user_shelude = day+":"+event_name+';'
                # print('добавляем календарь пользователя',user_shelude)
                await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, user_shelude,add=True)
                await context.bot.send_message(
                chat_id=user_id,
                text=f'Вы подписались на {event_name} в {translate_days_to_russian(day)}. Теперь вы будете получать уведомления накануне, чтобы ничего не пропустить.', reply_markup=InlineKeyboardMarkup(keyboard_start_old) 
            )

    #Отписка от дня пользователя       
    for day, events in events_schedule.items():
        for event_name,event_details in events.items():
            if choice == f"otpis_{day+event_name}":
                # user_shelude[day] = event_name
                user_shelude = day+":"+event_name
                # print('добавляем календарь пользователя',user_shelude)
                await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, user_shelude,add=False)
                await context.bot.send_message(
                chat_id=user_id,
                text=f'Вы отписались от {event_name} в {translate_days_to_russian(day)}. Теперь уведомления на этот день не будут приходить вам.', reply_markup=InlineKeyboardMarkup(keyboard_start_old) 
            )

    if choice == 'my_shelude':
        # Получаем список сообщений с клавиатурой для каждого события
        user_shelude_string = await get_user_sheluds(user_id)
        user_schedule = filter_calendar(events_schedule,user_shelude_string)
        # print('расписание пользователя',user_shelude_string)
        if user_shelude_string:
            messages_with_keyboard = format_events_schedule(user_schedule,Subscribe=False)
            # Отправляем каждое сообщение с клавиатурой
            for message, reply_markup in messages_with_keyboard:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            print('расписание пользователя пустое',user_shelude_string)
            await context.bot.send_message(
            chat_id=user_id,
            text=f"Вы не подписанны ни на один день занятий, пожалуйста выберите любой подходящий вам день из расписания.",
            reply_markup=InlineKeyboardMarkup(keyboard_start)
        )

    
    if choice == "try":
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Здорово! Будем ждать вас завтра  Отправим вам напоминание за {ShortTimeLimit[1]} часа до начала занятий"
        )
        await send_notifications_to_group_try(user_name)
        await context.bot.send_sticker(chat_id=user_id, sticker=yoga_sticker_id_love)
    
    if choice == "confirm": 
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Ваша Кундалини поднимается, увидимся через 🕐{time} часа",
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

    if choice == "shelude":
            # Получаем список сообщений с клавиатурой для каждого события
            messages_with_keyboard = format_events_schedule(events_schedule,Subscribe=True)
            # Отправляем каждое сообщение с клавиатурой
            for message, reply_markup in messages_with_keyboard:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

    




async def send_notifications_to_group_try(user_name):
    await bot.send_message(group_id, f"\n На завтра есть предварительная запись от {user_name}")

async def send_notifications_to_group_confirm(user_name):
    await bot.send_message(group_id, f"\n Сегодня есть подтвержденная запись от {user_name}")

async def send_notifications_to_group_sorry(user_name):
    await bot.send_message(group_id, f"\n {user_name} сегодня не сможет придти")


async def update_spreadsheet_data(application):
    # global send_messages_task
    await get_telegram_user_ids()


# Добавляем пользователей и их выбор в таблицу
async def update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, user_shelude,add=True):
    # Аутентификация в Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_API_CREDENTIALS_JSON, scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)
    user_ids,user_sheludes =  await get_telegram_user_ids()
    sheet = spreadsheet.get_worksheet(0)
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_data = sheet.get_all_values()
    user_exists = any(str(user_id) == user for user in user_ids)

    if user_exists:
        # print('пользователь есть',user_exists)
        for index, entry in enumerate(all_data):
            if entry[0] == str(user_id):
                if add:
                    if user_shelude in entry[2]:
                        pass
                    else:
                        entry[2] += user_shelude
                        sheet.update(f'A{index + 1}:C{index + 1}', [entry], value_input_option='USER_ENTERED')
                else:
                    if user_shelude in entry[2]:
                        entry[2] = entry[2].replace(user_shelude+';', '')
                        sheet.update(f'A{index + 1}:C{index + 1}', [entry], value_input_option='USER_ENTERED')
                    else:
                        pass                            
                
                break  # Завершаем цикл после обновления
    else:
        # print('такого пользователя нет')
        sheet.append_row([user_id, user_name, user_shelude])
    



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
    user_sheludes = await asyncio.to_thread(sheet.col_values, 3)

    # Фильтрация пользователей, оставляем только тех, у кого 3-ий столбец равен True
    # filtered_users = [user_id for user_id, agrees in zip(user_ids, user_agrees) if agrees.lower() == 'true']

    return user_ids,user_sheludes


# Получаем расписание пользвоателя
async def get_user_sheluds(user_id):
    user_shelude =''
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_API_CREDENTIALS_JSON, scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)

    # Аутентификация и открытие таблицы по идентификатору
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)

    # Получение активного листа (первого листа в таблице)
    sheet = spreadsheet.get_worksheet(0)
    all_data = sheet.get_all_values()

    for entry in all_data:
        if entry[0] == str(user_id):
            user_shelude = entry[2]
            # print('не пустое расписание',user_shelude)
        else: 
            # print('пустое расписание')
            user_shelude +=''

    return user_shelude


async def send_messages_to_users(event_text,event_shelude):
    # hours, minutes, eng_day, nearest_day = find_nearest_day(day_of_week_index)
    reply_markup = InlineKeyboardMarkup(keyboard22)

    try:
        user_ids,user_shelude_string = await get_telegram_user_ids()
        user_schedule_dict = dict(zip(user_ids, user_shelude_string))

        user_ids_filtred = [user_id for user_id, schedule in user_schedule_dict.items() if event_shelude in schedule]

        print('напоминанеи за 24 часа отфильтрованным пользователям',user_ids_filtred)

        for user_id in user_ids_filtred:
            # Send the reminder message
            await bot.send_message(user_id, f"\n Напоминание на завтра: \n {event_text} \n⚠️ Если вы собираетесь придти, пожалуйста нажмите кнопку - Пойду на занятие 👇 ", reply_markup=reply_markup)
    except Exception as e:
        print(f"Произошла ошибка при отправке сообщения: {e}")



async def send_reminder_to_users(event_text):
    reply_markup = InlineKeyboardMarkup(keyboard3)

    try:
        user_ids,filtered_users = await get_telegram_user_ids()
        print('Напоминание за 4 часа')
        for user_id in user_ids:
            # Send the reminder message
            await bot.send_message(user_id, f"\n Напоминаем, сегодня, через {ShortTimeLimit[1]} часа начнуться занятия \n {event_text}", reply_markup=reply_markup)
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
        asyncio.ensure_future(time_until_event())
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