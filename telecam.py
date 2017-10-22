import os
import logging
import time

from telegram.ext import Updater, CommandHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class TelecamException(Exception):
  pass

def hello(bot, update):
  bot.send_message(chat_id=update.message.chat_id, text="Hello World!")

def pic(bot, update):
  bot.send_message(chat_id=update.message.chat_id, text="pic")
  
def vid(bot, update):
  bot.send_message(chat_id=update.message.chat_id, text="vid")

class TelegramBot():
  def __init__(self, token=None):
  self.token = os.getenv("TELECAM_API_KEY") if token is None else token
  if self.token is None:
    raise TelecamException("No API Key found.")
  else:
    self.updater = Updater(token=self.token)

  def addHandler(self, cmd, func):
    self.updater.dispatcher.add_handler(CommandHandler(cmd, func))

  def addHandlers(self, pairs):
    for cmd, func in pairs:
      self.updater.dispatcher.add_handler(CommandHandler(cmd, func))

  def start():
    self.updater.start_polling()
  

def main():
  bot = TelegramBot()
  bot.addHandlers(func.__name__, func for func in (hello, pic, vid))
  bot.start()


if __name__ == "__main__":
  main()




