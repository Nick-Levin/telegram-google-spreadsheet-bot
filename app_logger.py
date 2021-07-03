#!/usr/bin/python3

# Logger docs https://www.toptal.com/python/in-depth-python-logging

from pathlib import Path
from configuration import Config
import logging

class AppLogger:
  _config = Config()
  _instance = None
  logger = None

  def __new__(cls):
    if AppLogger._instance is None:
      AppLogger._instance = object.__new__(cls)
    return AppLogger._instance

  def __init__(self):
    Path("logs").mkdir(parents=True, exist_ok=True)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(self._config.LOG_FORMAT_CONSOLE))
    file_handler = logging.FileHandler(self._config.LOG_FILE)
    file_handler.setFormatter(logging.Formatter(self._config.LOG_FORMAT_FILE))

    self.logger = logging.getLogger(__name__)
    self.logger.addHandler(console_handler)
    self.logger.addHandler(file_handler)
    self.logger.setLevel(self._config.LOG_LEVEL_APP)

  def get_logger(self):
    return self.logger
