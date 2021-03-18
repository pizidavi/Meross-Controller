import asyncio
import telepot
from telepot.namedtuple import InlineKeyboardMarkup
from datetime import datetime, timedelta

from lib.logger import get_logger
from control.Config import Config
from control.DAO import DAO
from app.view import View
from app.modal import Modal

logger = get_logger(__name__)
config = Config()


class App:

    def __init__(self, loop=None):
        self.__loop = asyncio.get_event_loop() if loop is None else loop
        self.__dao = None
        self.__bot = telepot.Bot(config.telegram.token)

        self.__view = View(self.__bot, self.__handler)

        self.__modal = Modal(config.meross, config.solaredge, config.sun)
        self.__loop.run_until_complete(self.__modal.async_init())

    def __handler(self, json: dict) -> None:
        if self.__dao is not None:
            self.__dao.close()
        self.__dao = DAO()
        flavor, glance = telepot.flance(json)

        from_id = str(json['from']['id'])
        user = self.__dao.search_user(from_id)
        if user is None:
            self.__bot.sendMessage(from_id, 'You cannot use this bot.')
            return

        if 'chat' in flavor:
            content_type, chat_type, chat_id = telepot.glance(json, flavor='chat')
            logger.info('%s %s %s', 'chat', chat_id, content_type)

            if content_type == 'text':
                if '/start' in json['text']:
                    message = self.__view.welcome(json['from']['first_name'])
                    self.__bot.sendMessage(chat_id, message)

                    devices = self.__dao.get_all_devices()
                    message, inline_keyboard = self.__view.menu(devices)
                    self.__bot.sendMessage(chat_id, message,
                                           reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                                           parse_mode='Markdown')
                else:
                    self.__bot.sendMessage(chat_id, 'Command not found')
            else:
                self.__bot.sendMessage(chat_id, 'Datatype not supported')

        elif 'callback_query' in flavor:
            query_id, from_id, query_data = telepot.glance(json, flavor='callback_query')
            chat_id, message_id = json['message']['chat']['id'], json['message']['message_id']
            logger.info('%s %s %s', 'callback_query', from_id, query_data)

            action = query_data.split('|')[0]
            data = query_data.split('|')[1:]

            if 'menu' == action:
                devices = self.__dao.get_all_devices()
                message, inline_keyboard = self.__view.menu(devices)
                self.__bot.editMessageText((chat_id, message_id), message,
                                           reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                                           parse_mode='Markdown')
            elif 'device' == action:
                """
                0: device_id
                1: day
                """
                self.__device(query_id, (chat_id, message_id), data)
            elif 'lock' == action:
                """
                0: device_id
                1: delay before unlock (optional)
                """
                if len(data) == 1:
                    message, inline_keyboard = self.__view.choose_delay(data[0])
                    self.__bot.editMessageText((chat_id, message_id), message,
                                               reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                                               parse_mode='Markdown')
                elif len(data) == 2:
                    self.__modal.lock_device(data[0], int(data[1]))
                    self.__device(query_id, (chat_id, message_id), [data[0], 0])
                    self.__bot.answerCallbackQuery(query_id, text='Dispositivo bloccato')
            elif 'unlock' == action:
                """
                0: device_id
                """
                self.__modal.unlock_device(data[0])
                self.__device(query_id, (chat_id, message_id), [data[0], 0])
                self.__bot.answerCallbackQuery(query_id, text='Dispositivo sbloccato')
            else:
                self.__bot.answerCallbackQuery(query_id, text='Command not found', show_alert=True)
            self.__bot.answerCallbackQuery(query_id)

    def __device(self, query_id, msg_identifier, data):
        date = datetime.today() + timedelta(days=int(data[1]))

        device = self.__modal.get_device(data[0])
        if device is None:  # get from db if not exist in modal
            device = self.__dao.get_device(data[0])
        powers_on = self.__dao.get_device_powers_on(data[0], date.strftime('%Y-%m-%d'))
        attributes = self.__dao.get_device_attributes(data[0])

        if device is not None:
            message, inline_keyboard = self.__view.device(device, powers_on, attributes, int(data[1]))
            self.__bot.editMessageText(msg_identifier, message,
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                                       parse_mode='Markdown')
        else:
            self.__bot.answerCallbackQuery(query_id, text='Device not found', show_alert=True)

    def close(self):
        self.__loop.run_until_complete(self.__modal.async_close())
