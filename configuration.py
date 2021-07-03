#!/usr/bin/python3

import configparser
from datetime import datetime

class Config(object):
  _instance = None
  
  def __new__(cls):
    if Config._instance is None:
      Config._instance = object.__new__(cls)
    return Config._instance

  def __init__(self):
    config = configparser.RawConfigParser()
    config.read('config.ini')

    self.LOG_FORMAT_FILE    = config["LOG"]["text_format_file"]
    self.LOG_FORMAT_CONSOLE = config["LOG"]["text_format_console"]
    self.LOG_DATE           = datetime.now().strftime(config["LOG"]["date_format"])
    self.LOG_FILE           = config["LOG"]["path"].replace("{DATE}", self.LOG_DATE)
    self.LOG_LEVEL_SYSTEM   = config["LOG"]["system_level"]
    self.LOG_LEVEL_APP      = config["LOG"]["app_level"]

    self.SPREADSHEET_ID     = config["GOOGLE"]["spreadsheet_id"]
    self.ROW_DATE_START     = config["GOOGLE"]["row_date_start"]
    self.ROW_NAMES          = config["GOOGLE"]["row_names_start"]

    self.REDIS_URL          = config['REDIS']['url']
    self.REDIS_PORT         = config['REDIS']['port']

    self.TELEBOT_API_KEY    = config['TELEGRAM']['api_key_path']

    # TODO: init logger HERE
    # TODO: log info for config loaded to cache
