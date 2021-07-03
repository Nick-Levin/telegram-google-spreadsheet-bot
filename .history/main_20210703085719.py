#!/usr/bin/python3

# google spreadsheet docs https://developers.google.com/sheets/api/quickstart/python
# gspread docs https://docs.gspread.org/en/latest/oauth2.html
# Logger docs https://www.toptal.com/python/in-depth-python-logging

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
ROW_DATE_START = config["GOOGLE"]["row_date_start"]
ROW_NAMES = config["GOOGLE"]["row_names_start"]

# Logger config
log_date = datetime.now().strftime(config["LOG"]["date_format"])
log_format = config["LOG"]["text_format"]
log_file = config["LOG"]["path"].replace("DATE", log_date)
log_level = config["LOG"]["level"]
logging.basicConfig(filename=log_file, format=log_format, level=log_level)

# Redis connection
redis = redis.Redis(config['REDIS']['url'], config['REDIS']['port'])
logging.info(f'connection to redis established on {config["REDIS"]["url"]}:{config["REDIS"]["port"]}')

# Timezone
client = ntplib.NTPClient()

# using global pool to get the closest server(not many in israel to sync time)
response = client.request('pool.ntp.org', version=3)
current_month: str = datetime.fromtimestamp(response.tx_time).strftime('%B')
current_day: int = int(datetime.fromtimestamp(response.tx_time).strftime('%d'))

# Main
cursor = 0
users = {}

while True:
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
  bot.reply_to(message, "Bot options are ['register', 'remove']")

@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(message, "Hello, you need to register send /register")

@bot.message_handler(commands=['register'])
def send_register(message):
  bot.reply_to(message, "What your full name?")
  redis.set("user/")

# TODO: add function to handler (Bot should react to users bad input)
@bot.message_handler(content_types=['text'], regexp='^(?:([01]?\d|2[0-3]):([0-5]?\d):)?([0-5]?\d)$')
def handle_hour_report(message):
  logging.debug(f'User: {message.from_user.username} entered time {message.text}')
  if message.from_user.username in users:
    gc = gspread.service_account(filename='service_account.json')
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(current_month)
    values = worksheet.get_all_values()
    update_row_number = ROW_DATE_START + current_day
    update_column_number = values[ROW_NAMES].index(users[message.from_user.username]) + 1
    worksheet.update_cell(update_row_number, update_column_number, message.text)

    bot.send_message(message.chat.id, 'successfully update!')
    logging.info(f'time updated for user {message.from_user.username}')
  else:
    bot.send_message(message.chat.id, f'user {message.from_user.username} not registered')
    logging.info(f'user {message.from_user.username} not registered')

# TODO: scheduled task runs once a day 5 times a week (scan blank table cells and send a reminder to the user)
# TODO: /register registration form
# TODO: /help list all commands

bot.polling()
