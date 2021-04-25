from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CallbackContext, Defaults

from lib.logger import get_logger
from control.Config import Config
from control.DAO import DAO
from app.view import View
from app.modal import Modal

logger = get_logger(__name__)
config = Config()


class App:

    def __init__(self, loop):
        self.__loop = loop
        self.__dao = None

        self.__updater = Updater(config.telegram.token, defaults=Defaults(parse_mode=ParseMode.MARKDOWN))
        self.__view = View(self.__updater, self.__handler)

        self.__modal = Modal(config.meross, config.solaredge, config.sun)
        self.__loop.run_until_complete(self.__modal.async_init())

    def __handler(self, update: Update, _: CallbackContext) -> None:
        if self.__dao is not None:
            self.__dao.close()
        self.__dao = DAO()

        user = update.effective_user
        search = self.__dao.search_user(user.id)
        if search is None:
            if update.message:
                update.message.reply_text('You cannot use this bot.')
            return

        if update.message:
            message = update.message
            logger.info('%s %s %s', 'chat', user.id, message.text)

            if '/start' in message.text:
                text = self.__view.welcome(user.first_name)
                message.reply_text(text)

                devices = self.__dao.get_all_devices()
                text, inline_keyboard = self.__view.menu(devices)
                message.reply_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard))
            else:
                message.reply_text('Command not found')

        elif update.callback_query:
            query = update.callback_query
            logger.info('%s %s %s', 'callback_query', user.id, query.data)

            action = query.data.split('|')[0]
            data = query.data.split('|')[1:]

            if 'menu' == action:
                devices = self.__dao.get_all_devices()
                text, inline_keyboard = self.__view.menu(devices)
                query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard))
            elif 'device' == action:
                """
                0: device_id
                1: day
                """
                self.__device(query, data[0], int(data[1]))
            elif 'lock' == action:
                """
                0: device_id
                1: delay before unlock (optional)
                """
                if len(data) == 1:
                    text, inline_keyboard = self.__view.choose_delay(data[0])
                    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard))
                elif len(data) == 2:
                    self.__modal.lock_device(data[0], int(data[1]))
                    self.__device(query, data[0], 0)
                    query.answer('Dispositivo bloccato')
            elif 'unlock' == action:
                """
                0: device_id
                """
                self.__modal.unlock_device(data[0])
                self.__device(query, data[0], 0)
                query.answer('Dispositivo sbloccato')
            else:
                query.answer('Command not found', show_alert=True)
            query.answer()

    def __device(self, query, device_id, day=0):
        date = datetime.today() + timedelta(days=day)

        _type = 'local'
        device = self.__modal.get_device(device_id)
        if device is None:  # get from DB if not exist
            _type = 'db'
            device = self.__dao.get_device(device_id)
        powers_on = self.__dao.get_device_powers_on(device_id, date.strftime('%Y-%m-%d'))
        attributes = self.__dao.get_device_attributes(device_id)

        if device is not None:
            text, inline_keyboard = self.__view.device(_type, device, powers_on, attributes, day)
            query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        else:
            query.answer('Device not found', show_alert=True)

    def close(self):
        self.__updater.stop()
        self.__loop.run_until_complete(self.__modal.async_close())
