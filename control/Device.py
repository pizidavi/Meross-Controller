import asyncio
from datetime import datetime, timedelta
from meross_iot.controller.mixins.electricity import ElectricityMixin
from meross_iot.model.enums import Namespace

import lib.Logging as Log
import control.controller as Controller

logger = Log.get_logger(__name__)


class Device:

    def __init__(self, device, **kwargs):
        self.__device = device
        self.__kwargs = kwargs

        self.__last_state = None
        self.__last_power_on = kwargs['lastPowerOn']

        self.__notification_register = False
        self.__register_push_notification()

    def get(self):
        return self.__device

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if not (key in self.__kwargs and value == self.__kwargs[key]):
                self.__kwargs[key] = value
                logger.info('UPDATED DEVICE %s: %s:%s', self.name, key, value)

    @property
    def id(self) -> int:
        return self.__kwargs['id']

    @property
    def uuid(self) -> str:
        return self.__device.uuid

    @property
    def name(self) -> str:
        return self.__device.name

    @property
    def type(self) -> str:
        return self.__device.type

    @property
    def current_power_usage(self) -> int:
        return self.__kwargs['currentPowerUsage']

    @property
    def solar_power_on(self) -> bool:
        return self.__kwargs['solarPowerOn']

    @property
    def times_always_on(self) -> list:
        return self.__kwargs['timesAlwaysOn']

    @property
    def firmware_version(self) -> str:
        return self.__device.fwversion

    @property
    def hardware_version(self) -> str:
        return self.__device.hwversion

    @property
    def is_on(self) -> bool:
        return self.__device.is_on()

    @property
    def next_power_status_change(self) -> datetime:
        return self.__last_power_on + self.__kwargs['timeDelayBeforePowerOff']

    @property
    def last_power_on(self) -> datetime:
        return self.__last_power_on

    @property
    def last_async_update_timestamp(self):
        return self.__device.last_full_update_timestamp

    async def async_update(self) -> None:
        if self.last_async_update_timestamp is None:
            await self.__device.async_update()
            self.__last_state = self.is_on

    def __register_push_notification(self) -> None:
        if not self.__notification_register:
            self.__device.register_push_notification_handler_coroutine(self.__notifications)
            self.__notification_register = True

    def __unregister_push_notification(self) -> None:
        if self.__notification_register:
            self.__device.unregister_push_notification_handler_coroutine(self.__notifications)
            self.__notification_register = False

    async def __notifications(self, namespace, data, device_internal_id) -> None:

        if namespace == Namespace.CONTROL_TOGGLEX:
            toggle = int(data['togglex'][0]['onoff'])
            if toggle != self.__last_state:
                logger.info(f'CONTROL_TOGGLEX {self.name} is %s', 'on' if toggle else 'off')

                asyncio.ensure_future(Controller.log(self.id, toggle))
                self.__last_state = toggle
                self.__last_power_on = datetime.now() if toggle else self.__last_power_on
            else:
                logger.debug(f'CONTROL_TOGGLEX {self.name}: Same state!')

        elif namespace == Namespace.SYSTEM_ALL:
            logger.debug(f'SYSTEM_ALL {self.name}: Updated all data')

        elif namespace == Namespace.SYSTEM_ONLINE:
            logger.warning(f'SYSTEM_ONLINE {self.name}: {data}')

        else:
            logger.debug(f'Notification: {namespace} {self.name}: {data}')

    async def async_get_instant_metrics(self):
        return await self.__device.async_get_instant_metrics() if isinstance(self.__device, ElectricityMixin) else None

    async def async_turn_on(self) -> None:
        await self.__device.async_turn_on()

    async def async_turn_off(self) -> None:
        await self.__device.async_turn_off()

    def __del__(self):
        self.__unregister_push_notification()

    def __str__(self):
        return f"{self.name} ({self.type}) - consumption {self.current_power_usage} W"
