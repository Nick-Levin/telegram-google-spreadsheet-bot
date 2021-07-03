#!/usr/bin/python3

# telegram bot docs https://github.com/eternnoir/pyTelegramBotAPI#a-simple-echo-bot
# google spreadsheet docs https://developers.google.com/sheets/api/quickstart/python
# gspread docs https://docs.gspread.org/en/latest/oauth2.html

import redis
import telebot
import ntplib
import gspread
from logging import Logger
from configuration import Config
from app_logger import AppLogger
from datetime import datetime
from pathlib import Path

# create logs folder
Path("logs").mkdir(parents=True, exist_ok=True)

config: Config = Config()
logger: Logger = AppLogger().get_logger()

# Redis connection
redis = redis.Redis(config.REDIS_URL, config.REDIS_PORT)
logger.info(f'connection to redis established on {config.REDIS_URL}:{config.REDIS_PORT}')

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

bot = telebot.TeleBot(redis.get(config.TELEBOT_API_KEY).decode())

# Telegram bot handlers
# TODO: add function to handler (Bot should react to users bad input)
@bot.message_handler(content_types=['text'], regexp='^(?:([01]?\d|2[0-3]):([0-5]?\d):)?([0-5]?\d)$')
def handle_hour_report(message):
  logger.debug(f'User: {message.from_user.username} entered time {message.text}')
  if message.from_user.username in users:
    gc = gspread.service_account(filename='service_account.json')
    sheet = gc.open_by_key(config.SPREADSHEET_ID)
    worksheet = sheet.worksheet(current_month)
    values = worksheet.get_all_values()
    update_row_number = config.ROW_DATE_START + current_day
    update_column_number = values[config.ROW_NAMES].index(users[message.from_user.username]) + 1
    worksheet.update_cell(update_row_number, update_column_number, message.text)

    bot.send_message(message.chat.id, 'successfully update!')
    logger.info(f'time updated for user {message.from_user.username}')
  else:
    bot.send_message(message.chat.id, f'user {message.from_user.username} not registered')
    logger.info(f'user {message.from_user.username} not registered')

# TODO: scheduled task runs once a day 5 times a week (scan blank table cells and send a reminder to the user)
# TODO: /register registration form
# TODO: /help list all commands

bot.polling()
