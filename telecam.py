#!/usr/bin/env python3
import os
import logging
import json
import argparse
from sys import stderr
from time import sleep
from functools import wraps 
from io import BytesIO
from picamera import PiCamera, Color
import datetime

import telegram
from telegram.ext import Updater, CommandHandler

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(name)s - %(message)s', level=logging.DEBUG, filename="telecam.log")

def cameraWrap(f, camera):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, camera=camera, **kwargs)
    return wrapper

def recordVideo(camera, buffer, length=10, timestamp=True):
    logging.info("Recording {}-sec video with{} timestamp".format(length, '' if timestamp else 'out'))
    camera.annotate_background = Color('black')
    camera.annotate_text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.debug("Annoation set up.")
    camera.start_recording(buffer, format='h264', quality=25)
    logging.debug("Recoding started.")
    start = datetime.datetime.now()
    while (datetime.datetime.now() - start).seconds < length:
        camera.annotate_text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        camera.wait_recording(0.2)
    camera.stop_recording() 
    logging.debug("Recoding done.")
    buffer.seek(0)

#
# callback funcs
#
def hello(bot, update, args=None):
    bot.send_message(chat_id=update.message.chat_id, text="Hello World!")

def picture(bot, update, args=None, camera=None):
    logging.info("Picture request.")
    bot.send_message(chat_id=update.message.chat_id, text="snapping pic...")
    #bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.UPLOAD_PHOTO)
    with BytesIO() as buffer:
        camera.annotate_text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        camera.capture(buffer, 'jpeg')
        buffer.seek(0)
        bot.send_photo(update.message.chat_id, photo=buffer)

 
def video(bot, update, args=None, camera=None):
    logging.info("Video request.")
    videoLength = 10
    if args:
        try: 
            videoLength = int(args[0])
            if videoLength < 0:
                videoLength = 1
            elif videoLength > 60:
                videoLength = 60
        except ValueError:
            videoLength = 10

    bot.send_message(chat_id=update.message.chat_id, text="recording {}-second video".format(videoLength))

    with BytesIO() as buffer:
        recordVideo(camera, buffer, videoLength)
        bot.send_video(update.message.chat_id, video=buffer)
        bot.send_message(chat_id=update.message.chat_id, text="video sent")


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="show commands")


class TelecamException(Exception):
    pass

class TelegramBot():
    def __init__(self, *, token=None, authorized_users=None, handlers=None, config=None, config_file=None):
        '''
            token: Telegram bot API token
            camera: PiCamera instance
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
            with PiCamera(resolution=(1280, 720), framerate=24) as camera:
                camera.annotate_text_size = 16
                cameraHandlers = {
                    'picture': picture, 'pic': picture,
                    'video': video,     'vid': video,
                }
                cameraHandlers = { name: cameraWrap(handler, camera) for name, handler in cameraHandlers.items() }
                textHandlers = {
                    'help': help,
                    'hello': hello
                }

                with TelegramBot(config_file=config_file, handlers={**cameraHandlers, **textHandlers}) as bot:
                    bot.start()
        except (TelecamException,KeyboardInterrupt) as e:
                print(e)
                raise e


if __name__ == "__main__":
    main()


