import os
import logging
import time
import functools
import json

from telegram.ext import Updater, CommandHandler

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(name)s - %(message)s', level=logging.INFO)


class TelecamException(Exception):
  pass

def hello(bot, update):
  bot.send_message(chat_id=update.message.chat_id, text="Hello World!")
  print("User: {}".format(update.effective_user.id))

def pic(bot, update):
  bot.send_message(chat_id=update.message.chat_id, text="pic")
 
def vid(bot, update):
  bot.send_message(chat_id=update.message.chat_id, text="vid")

class TelegramBot():
  def __init__(self, *, token=None, authorized_users=None, config=None, config_file=None):
    if config is not None:
      self.load_config(config)
    elif config_file is not None:
      self.load_config_from_file(config_file)
    else:
      if not any((token, authorized_users)):
        raise TelecamException("Either config or all other keyword-args must be provided.")
      else:
        self.token = token
        self.authorized_users = authorized_users

    self.updater = Updater(token=self.token)

  def addHandler(self, cmd, func, restricted=True):
    handler = self.restricted(func) if restricted else func
    self.updater.dispatcher.add_handler(CommandHandler(cmd, handler))

  def addHandlers(self, pairs, restricted=True):
    for cmd, func in pairs:
      handler = self.restricted(func) if restricted else func
      self.updater.dispatcher.add_handler(CommandHandler(cmd, handler))

  def start(self):
    self.updater.start_polling()
    self.updater.idle()
  
  def load_config(self, config):
    for attr in ('token', 'authorized_users'):
      setattr(self, attr, config[attr])

  def load_config_from_file(self, config_file):
    with open(config_file, 'r') as f:
      self.load_config(json.load(f))

  def restricted(self, func):
    @functools.wraps(func)
    def wrapper(bot, update, *args, **kwargs):
      user_id = update.effective_user.id
      if user_id not in self.authorized_users:
        logging.info("Unauthorized access denied for {}.".format(user_id))
        return
      return func(bot, update, *args, **kwargs)
    return wrapper


def main():
  config_file = os.getenv("TELECAM_CONFIG")
  bot = TelegramBot(config_file=config_file)
  bot.addHandlers((func.__name__, func) for func in (hello, pic, vid))
  bot.start()


if __name__ == "__main__":
  main()




