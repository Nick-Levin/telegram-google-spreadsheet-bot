#!/usr/bin/python3

# telegram bot docs https://github.com/eternnoir/pyTelegramBotAPI#a-simple-echo-bot
# google spreadsheet docs https://developers.google.com/sheets/api/quickstart/python
# gspread docs https://docs.gspread.org/en/latest/oauth2.html

import yaml
import telebot
import logging
import gspread
import configparser
from datetime import datetime
from pathlib import Path
from api_platform import API_Platform

# TODO: break the whole thing into classes
# TODO: read all hardcoded strings from config.yml

class Madock():
  def __init__(self):
    pass

# create logs folder
Path("logs").mkdir(parents=True, exist_ok=True)

# Config configuration
config = configparser.RawConfigParser()
config.read("config.ini")

# Constants
SPREADSHEET_ID = config["google"]["spreadsheet_id"]
ROW_DATE_START = config["google"]["row_date_start"]
ROW_NAMES = config["google"]["row_names_start"]

# Logger config
log_date = datetime.now().strftime(config["LOG"]["date_format"])
log_format = config["LOG"]["text_format"]
log_file = config["LOG"]["name"].replace("DATE", log_date)
log_level = config["LOG"]["level"]
logging.basicConfig(filename=log_file, format=log_format, level=log_level)

# functions
# TODO: move secret API key to mongoDB
def read_secret_file(platform: API_Platform):
  with open(f"secrets/secret_{platform.value}.key", "r") as secret_file:
    secret = secret_file.read().replace('\n', '')
    logging.debug(f'secret loaded to cache: {secret}')
    return secret

# TODO: move all users to mongoDB
def read_users_configuration():
  with open("users.yml", 'r') as stream:
    users = yaml.safe_load(stream)
    logging.debug(f'users list loaded to cache: {users}')
    return users

# Main
users = read_users_configuration()
api_key_telegram = read_secret_file(API_Platform.telegram)
bot = telebot.TeleBot(api_key_telegram)

# Telegram bot handlers
# TODO: add function to handler (Bot should react to users bad input)
@bot.message_handler(content_types=['text'], regexp='^(?:([01]?\d|2[0-3]):([0-5]?\d):)?([0-5]?\d)$')
def handle_hour_report(message):
  logging.debug(f'User: {message.from_user.username} entered time {message.text}')
  if message.from_user.username in users:

    gc = gspread.service_account(filename='service_account.json')
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(datetime.now().strftime("%B"))
    values = worksheet.get_all_values()
    update_row_number = ROW_DATE_START + int(datetime.now().strftime("%d"))
    update_column_number = values[ROW_NAMES].index(users[message.from_user.username]) + 1
    worksheet.update_cell(update_row_number, update_column_number, message.text)

    bot.send_message(message.chat.id, 'time updated')
    logging.info(f'time updated for user {message.from_user.username}')
  else:
    bot.send_message(message.chat.id, f'user {message.from_user.username} not registered')
    logging.info(f'user {message.from_user.username} not registered')

# TODO: scheduled task runs once a day 5 times a week (scan blank table cells and send a reminder to the user)
# TODO: /register registration form
# TODO: /help list all commands

bot.polling()
