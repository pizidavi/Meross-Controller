from telepot import Bot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton
from datetime import datetime, timedelta

from lib.logger import get_logger

logger = get_logger(__name__)


class View:

    def __init__(self, bot: Bot, handler):
        self.__bot = bot

        MessageLoop(self.__bot, handler).run_as_thread()
        logger.info('TelegramBot started')

    @staticmethod
    def welcome(first_name: str) -> str:
        message = 'Ciao {} 👋'.format(first_name)
        return message

    @staticmethod
    def menu(devices: list) -> tuple:
        message = 'Seleziona un dispositivo'
        inline_keyboard = [
            [InlineKeyboardButton(text='{ico} {name} {ico}'.format(ico=('❌' if r.boolDisable else ''), name=r.strName),
                                  callback_data='device|{}|{}'.format(r.intIdDevice, 0))] for r in devices
        ]

        return message, inline_keyboard

    @staticmethod
    def device(device, powers_on: list, attributes: list, day=0) -> tuple:
        date = datetime.today() + timedelta(days=int(day))

        device_id = device.id if hasattr(device, 'id') else device.intIdDevice
        name = device.name if hasattr(device, 'name') else device.strName
        current_power_usage = device.current_power_usage if hasattr(device, 'current_power_usage') else device.intUsage
        is_on = device.is_on if hasattr(device, 'is_on') else False
        is_locked = device.is_locked if hasattr(device, 'is_locked') else False
        lock_expire_at = device.lock_expire_at if hasattr(device, 'lock_expire_at') else None
        disabled = device.boolDisable if hasattr(device, 'boolDisable') else False  # from DAO

        message = '*{}* {}{}\n\n' \
                  'Stato: {}\n' \
                  'Consumo Teorico: {} W\n'\
            .format(name,
                    ('🔒' + (' | until ' + lock_expire_at.strftime('%H:%M') if lock_expire_at is not None else '')
                     if is_locked else ''),
                    ('- __Disabilitato__ ❌' if disabled else ''),
                    '🔴' if not is_on else '🔵',
                    current_power_usage)

        for _row in attributes:
            message += '{} {}\n'.format(_row.strText, _row.strValue)

        message += '\nAccensioni di _{}_:\n'.format('Oggi' if day == 0 else date.strftime('%d-%m-%Y'))
        for _row in powers_on:
            state = _row.boolState
            message += (' - ' if not state else '') + _row.dtaDate.strftime('%H:%M:%S') + ('\n' if not state else '')

        button = [InlineKeyboardButton(text='◀️', callback_data='device|{}|{}'.format(device_id, day - 1))]
        if day < 0:
            button.append(InlineKeyboardButton(text='▶️', callback_data='device|{}|{}'.format(device_id, day + 1)))

        inline_keyboard = [button]
        if not disabled:
            inline_keyboard.append([InlineKeyboardButton(text=('🔓 Unlock' if is_locked else '🔒 Lock'),
                                      callback_data='{}|{}'.format(('unlock' if is_locked else 'lock'), device_id))])
        inline_keyboard.append([InlineKeyboardButton(text='⬅️ Indietro', callback_data='menu')])
        return message, inline_keyboard

    @staticmethod
    def choose_delay(device_id) -> tuple:
        message = 'Per quante ore bloccare il dispositivo?'
        inline_keyboard = [
            [
                InlineKeyboardButton(text=str(x),
                                     callback_data='lock|{}|{}'.format(device_id, x * 60 * 60)) for x in range(2, 7)
            ],
            [InlineKeyboardButton(text='Sempre', callback_data='lock|{}|{}'.format(device_id, 0, 0))],
            [InlineKeyboardButton(text='⬅️ Indietro', callback_data='device|{}|{}'.format(device_id, 0))]
        ]
        return message, inline_keyboard
