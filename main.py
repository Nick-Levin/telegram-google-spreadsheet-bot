#!/usr/bin/python3

# google spreadsheet docs https://developers.google.com/sheets/api/quickstart/python
# gspread docs https://docs.gspread.org/en/latest/oauth2.html
# Logger docs https://www.toptal.com/python/in-depth-python-logging

import re
import redis
import telebot
import ntplib
import logging
import gspread
import configparser
from datetime import datetime
from pathlib import Path

# TODO: break the whole thing into classes

# create logs folder
Path("logs").mkdir(parents=True, exist_ok=True)

# Config initialization
config = configparser.RawConfigParser()
config.read("config.ini")

# Constants
SPREADSHEET_ID = config["GOOGLE"]["spreadsheet_id"]
ROW_DATE_START = int(config["GOOGLE"]["row_date_start"])
ROW_NAMES = int(config["GOOGLE"]["row_names_start"])

# Logger config
log_date = datetime.now().strftime(config["LOG"]["date_format"])
log_format = config["LOG"]["text_format"]
log_file = config["LOG"]["path"].replace("DATE", log_date)
log_level = config["LOG"]["level"]
logging.basicConfig(filename=log_file, format=log_format, level=log_level)

# Redis connection
redis = redis.Redis(config['REDIS']['url'], config['REDIS']['port'])
logging.info(
    f'connection to redis established on {config["REDIS"]["url"]}:{config["REDIS"]["port"]}')

# Timezone
client = ntplib.NTPClient()

# using global pool to get the closest server(not many in israel to sync time)
response = client.request('pool.ntp.org', version=3)
current_month: str = datetime.fromtimestamp(response.tx_time).strftime('%B')
current_day = int(datetime.fromtimestamp(response.tx_time).strftime('%d'))
current_day_name: str = datetime.fromtimestamp(response.tx_time).strftime('%A')
current_hour: int = datetime.fromtimestamp(response.tx_time).strftime('%H')

days_of_the_week = ['Sunday',
                    'Monday',
                    'Tuesday',
                    'Wednesday',
                    'Thursday',
                    'Friday']

# Main
cursor = 0
users = {}
global chat_id

while True:
    chat_id = redis.get('chat_info/')
    result = redis.scan(cursor, match='user/*', count=10)
    cursor = int(result[0])
    keys = result[1]
    for key in keys:
        users[key.decode()[5:]] = redis.get(key).decode()
    if cursor == 0:
        break

bot = telebot.TeleBot(redis.get(config['TELEGRAM']['api_key_path']).decode())

# Telegram bot handlers


@bot.message_handler(commands=['help'])
def handle_start_help(message):
    try:
        bot.reply_to(message, "Bot options are ['register', 'hours', 'ping']")
    except Exception as e:
        logging.error(e)
        bot.reply_to(message, "Something went wrong")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(message, 'Hello, you need to register send /register')
        redis.set('chat_info/', message.chat.id)
        logging.info('Chat ID:', message.chat.id)
    except Exception as e:
        logging.error(e)
        bot.reply_to(message, 'Something went wrong')


@bot.message_handler(commands=['ping'])
def send_welcome(message):
    try:
        bot.reply_to(message, 'PONG \o/')
    except Exception as e:
        logging.error(e)
        bot.reply_to(message, 'Something went wrong')


if current_day_name in days_of_the_week:
    if current_hour == 20:
        # TODO: add logic ignore if already set hours for today
        # TODO: put in a loop and sleep
        try:
            bot.send_message(
                chat_id, 'Reminder: How many hours you worked today?')
        except Exception as e:
            logging.error(e)
            bot.send_message(chat_id, 'Something went wrong')


@bot.message_handler(commands=['register'], content_types=['text'])
def send_register(message):
    try:
        logging.info(message.text, message.from_user.username)
        full_name = message.text[10:]
        if full_name.replace(" ", "").isalpha():
            redis.set(f'user/{message.from_user.username}', full_name)
            bot.reply_to(message, f'Welcome {full_name} :)')
        else:
            bot.reply_to(message, 'invalid name!')
    except Exception as e:
        logging.error(e)
        bot.reply_to(message, 'Something went wrong')


@bot.message_handler(commands=['hours'], content_types=['text'])
def handle_hour_report(message):
    try:
        if not re.search('^(?:([01]?\d|2[0-3]):([0-5]?\d):)?([0-5]?\d)$', message.text[7:]):
            bot.reply_to(message, f"Sorry I didn't understand that {message.text[7:]}")
        else:
            logging.debug(
                f'User: {message.from_user.username} entered time {message.text}')

            if current_day_name not in days_of_the_week:
                bot.send_message(chat_id, 'Shabat Hayom!')

            elif message.from_user.username in users:
                gc = gspread.service_account(filename='service_account.json')
                sh = gc.open_by_key(SPREADSHEET_ID)
                worksheet = sh.worksheet(current_month)
                values = worksheet.get_all_values()
                update_row_number = ROW_DATE_START + current_day
                update_column_number = values[ROW_NAMES].index(
                    users[message.from_user.username]) + 1
                worksheet.update_cell(
                    update_row_number, update_column_number, message.text)
                bot.send_message(message.chat.id, 'successfully update!')
                logging.info(
                    f'time updated for user {message.from_user.username}')
            else:
                bot.send_message(
                    message.chat.id, f'user {message.from_user.username} not registered, use the /register commnad for example /register Firstname Lastname')
                logging.info(
                    f'user {message.from_user.username} not registered')
    except Exception as e:
        logging.error(e)
        print(e)
        bot.reply_to(message, 'Something went wrong')

# TODO: scheduled task runs once a day 5 times a week (scan blank table cells and send a reminder to the user)
# TODO: chat_id per user atm it's overrides


bot.polling()
