import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

import lib.Logging as Log
from lib.Config import Config
from control.DAO import DAO

logger = Log.get_logger(__name__)
config = Config()


class TelegramBot:

    def __init__(self):
        self.__bot = telepot.Bot(config.telegram.token)
        self.__dao = None

        MessageLoop(self.__bot, self.__handler).run_as_thread()
        logger.info('TelegramBot started')

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
            self.__on_chat_message(json)
        elif 'callback_query' in flavor:
            self.__on_callback_query(json)

    def __on_chat_message(self, json: dict) -> None:
        content_type, chat_type, chat_id = telepot.glance(json, flavor='chat')
        logger.info("TelegramBot: %s %s", chat_id, content_type)

        def menu():
            devices = self.__dao.get_all_devices()

            message = 'Seleziona un dispositivo'
            inline_keyboard = []
            for row in devices:
                inline_keyboard.append(
                    [InlineKeyboardButton(
                        text=('❌ ' if row.boolDisable else '') + row.strName + ('❌ ' if row.boolDisable else ''),
                        callback_data='device|{}|{}'.format(row.intIdDevice, 0))]
                )
            self.__bot.sendMessage(chat_id, message,
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                                   parse_mode='Markdown')

        if content_type == 'text':
            if '/start' in json['text']:
                self.__bot.sendMessage(chat_id, 'Ciao {} 👋'.format(json['from']['first_name']))
                menu()
            else:
                self.__bot.sendMessage(chat_id, 'Command not found')

        else:
            self.__bot.sendMessage(chat_id, 'Datatype not supported')

    def __on_callback_query(self, json: dict) -> None:
        query_id, from_id, query_data = telepot.glance(json, flavor='callback_query')
        chat_id, message_id = json['message']['chat']['id'], json['message']['message_id']
        logger.info("TelegramBot: %s %s %s", from_id, 'callback_query', query_data)

        def menu():
            devices = self.__dao.get_all_devices()

            message = 'Seleziona un dispositivo'
            inline_keyboard = []
            for row in devices:
                inline_keyboard.append(
                    [InlineKeyboardButton(
                        text=('❌ ' if row.boolDisable else '') + row.strName + ('❌ ' if row.boolDisable else ''),
                        callback_data='device|{}|{}'.format(row.intIdDevice, 0))]
                )
            self.__bot.editMessageText((chat_id, message_id), message,
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                                       parse_mode='Markdown')

        def device(device_id, day=0):
            date = datetime.today() + timedelta(days=int(day))
            device = self.__dao.get_device(device_id)

            if device is None:
                self.__bot.answerCallbackQuery(query_id, text='Device not found', show_alert=True)
                return

            message = "*{}* {}\n\n" \
                      "Stato: {}\n" \
                      "Consumo Teorico: {} W\n\n" \
                      "Accensioni di _{}_:\n".format(device.strName,
                                                     " - Disabilitato ❌" if device.boolDisable else "",
                                                     "🔴" if not device.boolState else "🔵",
                                                     device.intUsage,
                                                     "Oggi" if day == 0 else date.strftime('%d-%m-%Y')
                                                     )
            for _row in self.__dao.get_device_powers_on(device_id, date.strftime('%Y-%m-%d')):
                message += (' - ' if not _row.boolState else "") + _row.dtaDate.strftime('%H:%M:%S') + (
                    "\n" if not _row.boolState else "")

            button = [
                InlineKeyboardButton(text='◀️', callback_data='device|{}|{}'.format(device_id, day - 1))
            ]
            if day < 0:
                button.append(
                    InlineKeyboardButton(text='▶️', callback_data='device|{}|{}'.format(device_id, day + 1))
                )
            inline_keyboard = [
                button,
                [InlineKeyboardButton(text='⬅️ Indietro', callback_data='menu')]
            ]
            self.__bot.editMessageText((chat_id, message_id), message,
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                                       parse_mode='Markdown')

        if 'menu' in query_data:
            menu()
        elif 'device' in query_data:
            device(query_data.split('|')[1], int(query_data.split('|')[2]))
        else:
            self.__bot.answerCallbackQuery(query_id, text='Command not found')

        self.__bot.answerCallbackQuery(query_id)

    def close(self):
        pass
