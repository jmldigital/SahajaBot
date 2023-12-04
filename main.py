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

    "Monday": {
        "Занятие для новичков": {
        "🕐": time(15, 25),
        "📍": "Офис, ул. 20-летия Октября, 59 оф.317, 3-й этаж \n https://yandex.ru/maps/-/CDe-b2ij",
        "🧘🏻‍♀️": "Практика медитации"
        },
        "Занятие для продолжающих": {
        "🕐": time(14, 25),
        "📍": "Офис, ул. 20-летия Октября, 59 оф.317, 3-й этаж \n https://yandex.ru/maps/-/CDe-b2ij",
        "🧘🏻‍♀️": "Практика медитации, методики очистки",
        }
        # "Занятие для мастеров": {
        # "🕐": time(15, 35),
        # "📍": "Офис, ул. 20-летия Октября, 59 оф.317, 3-й этаж \n https://yandex.ru/maps/-/CDe-b2ij",
        # "🧘🏻‍♀️": "Практика медитации, методики очистки",
        # }

    }

}

def format_events_schedule(events_schedule):
    result = ""
    for day, events in events_schedule.items():
        result += f"{translate_days_to_russian(day)}:\n"
        for event_name, event_details in events.items():
            result += f"  {event_name}:\n"
            for key, value in event_details.items():
                if isinstance(value, time):
                    formatted_time = value.strftime("%H:%M")
                    result += f"    {key}: {formatted_time}\n"
                else:
                    result += f"    {key}: {value}\n"
        result += "\n"
    return result



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



async def time_until_event(sent=True):
    # Получение текущего времени
    current_time = datetime.now()
    # day_of_week_index = current_time.weekday()
    near_opis =''
    near_geo =''
    near_title = ''
    nearest_time_delta = float('inf')
    # Рассчет времени до каждого мероприятия
    for day, events in events_schedule.items():
        for event_name, event_info in events.items():
            event_time = event_info.get("🕐")

            # Время мероприятия
            event_datetime = datetime.combine((current_time + timedelta(days=(get_day_index(day) - current_time.weekday() + 7) % 7)).date(), event_time)
            # event_datetime = event_datetime.total_seconds() / 3600
            print('время мероприятия',type(event_datetime))
            # Рассчет разницы во времени
            time_difference = (event_datetime - current_time).total_seconds() / 3600
            print('сейчас-',current_time, '-time_difference',time_difference )

            #Получаем ближайшее мероприятие
            if time_difference  < nearest_time_delta and time_difference >= ShortTimeLimit[1]:
                nearest_time_delta = time_difference
                near_title ="🚀 "+ event_name
                near_day = "🗓 " + translate_days_to_russian(day) + " 🕐"+ str(event_time)
                near_geo = "📍 "+ event_info.get("📍")
                near_opis = "🧘🏻‍♀️ "+ event_info.get("🧘🏻‍♀️")

                # nearest_output_string = near_title + '\n'+ "🗓 "+ translate_days_to_russian(day) + str(near_time) + '\n'+ near_geo + '\n' + near_opis
            if sent==True:
                if time_difference //1 == BigTimeLimit[1]:
                    await send_messages_to_users(near_title,near_day,near_geo,near_opis)
                if time_difference //1 == ShortTimeLimit[1]:
                    await send_reminder_to_users(near_title,near_day,near_geo,near_opis)
            else:
                pass

    print('ближайшая дельта',nearest_time_delta,'ближайший день',near_day,'ближайшее занятие',near_title)
    return near_title,near_day,near_geo,near_opis






# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


keyboard = [
    [
        InlineKeyboardButton("Подписаться на рассылку", callback_data="yes"),
        InlineKeyboardButton("Расписание", callback_data="shelude")
    ]
]

keyboard2 = [
    [
        InlineKeyboardButton("Расписание", callback_data="shelude"),
        InlineKeyboardButton("Отписаться от рассылки", callback_data="otpis"),
    ]

]

keyboard22 = [
    [
        InlineKeyboardButton("Пойду на занятие", callback_data="try"),
        InlineKeyboardButton("Расписание", callback_data="shelude"),
    ],
        [InlineKeyboardButton("Отписаться от рассылки", callback_data="otpis")]
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
        await update.message.reply_text('''Привет! мы Сахаджа Йоги города Воронеж сделали этого бота, чтобы напомнить всем желающим где и когда проходят регулярные бесплатные занятия по Сахадж-медитации. 

Вы можете подписаться на рассылку и бот будет присылать вам уведомления за 24 часа до начала занятий с информацией где и во сколько будет проходить ближайшее занятие, чтобы вы ничего не пропустили. Вы так же можете посмотреть актуальное расписание занятий, нажав на кнопку ниже 👇.''', reply_markup=reply_markup)
    

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    user_id = query.from_user.id
    user_ids,filtered_users = await get_telegram_user_ids()
    user_name = query.from_user.username
    choice = query.data


    # CallbackQueries need to be answered, even if no notification to the user is needed
    await query.answer()

    # Добавить пользователя в Google Таблицу
    if choice == "yes":
        if str(user_id) in user_ids:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Вы уже подписаны на мероприятия"
            )
        else:
            near_title,near_day,near_geo,near_opis = await time_until_event(sent=False)
            await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice==False, confirmation=False ,typeOf=True)
            await update_spreadsheet_data(context.application)    
            await context.bot.send_message(
                chat_id=user_id,
                text=f'''Спасибо, что подписались! Мы будем Вас уведомлять о предстоящих занятиях по медитации, что бы вы ничего не пропустили. 
                
Ближайшее мероприятие: 

{near_title} \n{near_day} \n{near_geo}.''' ,
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
        near_title,near_day,near_geo,near_opis = await time_until_event(sent=False)
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=False, typeOf=False)
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=False, typeOf=True)
        await update_spreadsheet_data(context.application)    
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Здорово! Будем ждать вас завтра в \n{near_day} по адресу \n{near_geo}. \n⏰ Отправим вам напоминание за {ShortTimeLimit[1]} часа до начала занятий"
        )
        await send_notifications_to_group_try(user_name)
        await context.bot.send_sticker(chat_id=user_id, sticker=yoga_sticker_id_love)
    
    if choice == "confirm":
        near_title,near_day,near_geo,near_opis = await time_until_event(sent=False)
        time = near_day[1:]
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=False, typeOf=False)
        await update_spreadsheet(user_id, user_name,  GOOGLE_SHEETS_SPREADSHEET_ID, choice=True, confirmation=True, typeOf=True)
        await update_spreadsheet_data(context.application)    
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Ваша Кундалини поднимается, увидимся в {near_geo} в 🕐{time}",
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
        await context.bot.send_message(
            chat_id=user_id,
            text=format_events_schedule(events_schedule)
        )


async def send_notifications_to_group_try(user_name):
    near_title,near_day,near_geo,near_opis = await time_until_event(sent=False)
    await bot.send_message(group_id, f"\n На {near_day} \n есть пердварительная запись от {user_name}")

async def send_notifications_to_group_confirm(user_name):
    near_title,near_day,near_geo,near_opis = await time_until_event(sent=False)
    await bot.send_message(group_id, f"\n На {near_day} \n есть подтвержденная запись от {user_name}")

async def send_notifications_to_group_sorry(user_name):
    near_title,near_day,near_geo,near_opis = await time_until_event(sent=False)
    await bot.send_message(group_id, f"\n На {near_day} \n {user_name} не сможет придти")


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

    return user_ids,filtered_users


async def send_messages_to_users(near_title,near_day,near_geo,near_opis):
    # hours, minutes, eng_day, nearest_day = find_nearest_day(day_of_week_index)
    reply_markup = InlineKeyboardMarkup(keyboard22)

    try:
        user_ids,filtered_users = await get_telegram_user_ids()
        print("Напоминание за 24 часа")
        for user_id in user_ids:
            # Send the reminder message
            await bot.send_message(user_id, f"\n Напоминание на завтра: \n{near_day} \n{near_title}, \n{near_geo}, \n{near_opis} \n⚠️ Если вы собираетесь придти, пожалуйста нажмите кнопку - Пойду на занятие 👇 ", reply_markup=reply_markup)
            # await bot.send_message(user_id, f"\n Напоминаем." , reply_markup=reply_markup)
    except Exception as e:
        print(f"Произошла ошибка при отправке сообщения: {e}")



async def send_reminder_to_users(near_title,near_day,near_geo,near_opis):
    reply_markup = InlineKeyboardMarkup(keyboard3)

    try:
        user_ids,filtered_users = await get_telegram_user_ids()
        print('Напоминание за 4 часа')
        for user_id in user_ids:
            # Send the reminder message
            await bot.send_message(user_id, f"\n Напоминаем, сегодня, через {ShortTimeLimit[1]} часа начнуться занятия \n {near_day} \n {near_title}, \n {near_geo}, \n {near_opis}", reply_markup=reply_markup)
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
        asyncio.ensure_future(time_until_event(sent=True))
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