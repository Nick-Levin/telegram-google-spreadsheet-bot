#!/usr/bin/python3

# telegram bot docs https://github.com/eternnoir/pyTelegramBotAPI#a-simple-echo-bot
# google spreadsheet docs https://developers.google.com/sheets/api/quickstart/python
# gspread docs https://docs.gspread.org/en/latest/oauth2.html

import yaml
import telebot
import logging
import gspread
from datetime import datetime
from api_platform import API_Platform

# Constants
SPREADSHEET_TOKEN_FILE = 'token.json'
SPREADSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '19fDDq9QyoN9aM-LnyCN7dbMynuD7yjMrvTSoizU_VZE'
SPREADSHEET_RANGE = 'B6:H12'
ROW_DATE_START = 5
ROW_NAMES = 4

# Logger config
log_date = datetime.now().strftime("%m%d%-y-%H:%M:%S")
log_format = '%(levelname)s:%(asctime)s:%(message)s'
log_file = f'logs/app-{log_date}.log'
log_level = logging.DEBUG
logging.basicConfig(filename=log_file, format=log_format, level=log_level)

# functions
def read_secret_file(platform: API_Platform):
  with open(f"secrets/secret_{platform.value}.key", "r") as secret_file:
    secret = secret_file.read().replace('\n', '')
    logging.debug(f'secret loaded to cache: {secret}')
    return secret

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

# TODO: /register registration form
# TODO: /help list all commands

bot.polling()
