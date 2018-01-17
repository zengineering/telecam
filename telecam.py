#!/usr/bin/env python3
import os
import logging
import json
import argparse
from sys import stderr
from time import sleep
from functools import wraps 
from io import BytesIO
from picamera import PiCamera

import telegram
from telegram.ext import Updater, CommandHandler

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(name)s - %(message)s', level=logging.INFO, filename="telecam.log")

#
# callback funcs
#
def hello(bot, update, args=None):
    bot.send_message(chat_id=update.message.chat_id, text="Hello World!")

def picture(bot, update, args=None):
    bot.send_message(chat_id=update.message.chat_id, text="pic: ({})".format(','.join(args)))
 
def video(bot, update, args=None):
    bot.send_message(chat_id=update.message.chat_id, text="video: ({})".format(','.join(args)))
    #bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.RECORD_VIDEO)
    sleep(2)
    bot.send_message(chat_id=update.message.chat_id, text="video done")

def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="show commands")


class TelecamException(Exception):
    pass

class TelegramBot():
    def __init__(self, *, token=None, authorized_users=None, handlers=None, config=None, config_file=None):
        '''
            token: Telegram bot API token
            authorized_users: List of authorized user IDs. 
                              Communication from all other users is logged, then ignored.
            handlers: List of command handlers (callback functions)
            namedHandlers: Dict of {command name: handler}
            config: Dict of other arguments (token, authorized_users)
            config_file: Json file from which to read config dict
        '''
        if config is not None:
            self.loadConfig(config)
        elif config_file is not None:
            self.loadConfigFromFile(config_file)
        else:
            if not any((token, authorized_users)):
                raise TelecamException("Either config or 'token' and 'authorized_users' args must be provided.")
            else:
                self.token = token
                self.authorized_users = authorized_users

        self.updater = Updater(token=self.token)

        if handlers is not None:
            for name, cb in handlers.items():
                self.addHandler(name, cb)

        
    def __enter__(self):
        return self

    def __exit__(self, excType, excValue, excTrace):
        self.updater.stop()

    def addHandler(self, cmd, func, restricted=True, passArgs=True):
        handler = self.restricted(func) if restricted else func
        self.updater.dispatcher.add_handler(CommandHandler(cmd, handler, pass_args=passArgs))

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
        @wraps(func)
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
    print("Starting telecam.")
    args = parseArgs()
    config_file = args.config
    if config_file is None:
        print("No config file found. Is the environment variable TELECAM_CONFIG set?", file=stderr)
    else:
        try:
            print("Starting Bot.")
            handlers = {
                'picture': picture, 'pic': picture,
                'video': video, 'vid': video,
                'help': help
            }
            with PiCamera() as camera:
                with TelegramBot(config_file=config_file, handlers=handlers) as bot:
                    bot.addHandler('hello', hello)
                    bot.start()
        except (TelecamException,KeyboardInterrupt) as e:
                print(e)


if __name__ == "__main__":
    main()


