#!/usr/bin/env python3
import os
import logging
import time
import functools
import json
import sys
import argparse

from telegram.ext import Updater, CommandHandler

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(name)s - %(message)s', level=logging.INFO, filename="telecam.log")


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
            self.loadConfig(config)
        elif config_file is not None:
            self.loadConfigFromFile(config_file)
        else:
            if not any((token, authorized_users)):
                raise TelecamException("Either config or all other keyword-args must be provided.")
            else:
                self.token = token
                self.authorized_users = authorized_users

        self.updater = Updater(token=self.token)
        
    def __enter__(self):
        return self

    def __exit__(self):
        self.updater.stop()

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
    
    def loadConfig(self, config):
        for attr in ('token', 'authorized_users'):
            setattr(self, attr, config[attr])

    def loadConfigFromFile(self, config_file):
        with open(config_file, 'r') as f:
            self.loadConfig(json.load(f))

    def restricted(self, func):
        @functools.wraps(func)
        def wrapper(bot, update, *args, **kwargs):
            user_id = update.effective_user.id
            if user_id not in self.authorized_users:
                logging.info("Unauthorized access denied for {}.".format(user_id))
                return
            return func(bot, update, *args, **kwargs)
        return wrapper


def parseArgs():
    parser = argparse.ArgumentParser(description="Telegram camera interface.")
    parser.add_argument("--config", required=False, default=os.getenv("TELECAM_CONFIG"), help="Config file")
    return parser.parse_args()

def main():
    #config_file = os.getenv("TELECAM_CONFIG")
    args = parseArgs()
    config_file = args.config
    if config_file is None:
        print("No config file found. Is the environment variable TELECAM_CONFIG set?", file=sys.stderr)
    else:
        try:
            print("Starting telecam.")
            with TelegramBot(config_file=config_file) as bot:
                print("token: {}\nauthorized_users: {}".format(bot.token, bot.authorized_users))
                bot.addHandlers((func.__name__, func) for func in (hello, pic, vid))
                bot.start()
        except TelecamException as e:
                print(e)
        except KeyboardInterruptException:
            pass


if __name__ == "__main__":
    main()


