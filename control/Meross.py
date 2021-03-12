from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
from meross_iot.model.enums import OnlineStatus

from lib.logger import get_logger
from obj.Device import Device
import control.controller as controller

logger = get_logger(__name__)


class Meross:

    def __init__(self, email, password):
        self.__email = email
        self.__password = password

        self.__http_client = None
        self.__manager = None

        self.__devices = []

    async def async_init(self) -> None:
        self.__http_client = await MerossHttpClient.async_from_user_password(email=self.__email,
                                                                             password=self.__password)
        self.__manager = MerossManager(http_client=self.__http_client)
        await self.__manager.async_init()
        await self.__manager.async_device_discovery()

    def get_device(self, device_id: int) -> Device or None:
        for device in self.__devices:
            if str(device.id) == str(device_id):
                return device
        return None

    def find_devices(self) -> list[Device]:
        global_devices = controller.get_devices()

        if not len(global_devices):
            logger.warning('FIND_DEVICES: no devices')
            return self.__devices

        for global_device in global_devices:
            device = self.__manager.find_devices(device_name=global_device['name'],
                                                 online_status=OnlineStatus.ONLINE)
            device = device[0] if len(device) else None

            obj = None
            for d in self.__devices:  # Find in local
                # obj = d if global_device['name'] == d.name else obj
                if global_device['name'] == d.name:
                    obj = d
                    break

            if global_device['disabled'] or (obj is not None and device is None):  # Remove device
                if obj is not None:
                    if device is None:
                        logger.warning('LOST DEVICE: %s', global_device['name'])
                    else:
                        logger.info('REMOVED DEVICE: %s', global_device['name'])
                    obj.__del__()
                    self.__devices.remove(obj)

            elif obj is None and device is not None:  # Add new device
                logger.info('ADDED DEVICE: %s', global_device['name'])
                logger.debug(f'DEVICE DATA: {global_device}')

                self.__devices.append(
                    Device(device,
                           id=global_device['id'],
                           currentPowerUsage=global_device['currentPowerUsage'],
                           solarPowerOn=global_device['solarPowerOn'],
                           timesAlwaysOn=global_device['timesAlwaysOn'],
                           timeDelayBeforePowerOff=global_device['timeDelayBeforePowerOff'],
                           lastPowerOn=global_device['lastPowerOn']
                           )
                )

            elif obj is not None and device is not None:  # Update device
                obj.update(
                    currentPowerUsage=global_device['currentPowerUsage'],
                    solarPowerOn=global_device['solarPowerOn'],
                    timesAlwaysOn=global_device['timesAlwaysOn'],
                    timeDelayBeforePowerOff=global_device['timeDelayBeforePowerOff']
                )

        return self.__devices

    async def async_stop(self) -> None:
        for device in self.__devices:
            device.__del__()

        self.__manager.close()
        await self.__http_client.async_logout()
