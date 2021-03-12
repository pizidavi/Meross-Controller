import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from lib.logger import get_logger
from control.Meross import Meross
from lib.SolarEdge import SolarEdge

# Logging
logging.getLogger('meross_iot').setLevel(logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

logger = get_logger(__name__)


class Modal:

    def __init__(self, meross, solaredge, sun):
        self.__sun = sun
        self.__home_default_load = solaredge.home_default_load

        self.__manager = Meross(meross.email, meross.password)
        self.__solaredge = SolarEdge(solaredge.api_token, solaredge.site_id)

        self.__scheduler = AsyncIOScheduler()
        self.__scheduler.add_job(self.__async_loop, 'interval', minutes=5)

    async def async_init(self) -> None:
        logger.info('MerossController started')
        self.__scheduler.start()
        await self.__manager.async_init()
        await self.__async_loop()

    async def __async_loop(self):
        now = datetime.now()

        devices = self.__manager.find_devices()
        if not len(devices):
            return

        result = self.__solaredge.get_current_power_flow(sunrise=self.__sun.sunrise, sunset=self.__sun.sunset)
        power_produced = (result['PV'] - result['LOAD']) if result else -self.__home_default_load
        logger.info(f"Remaining power: {power_produced} W")

        for device in devices:
            await device.async_update()  # Update device information
            if device.is_locked:  # Ignore locked device
                logger.debug('%s ignored because locked', device.name)
                continue

            time_always_on = False
            for time in device.times_always_on:
                if time['start'] <= now.time() < time['end']:  # Check All Times Always On
                    time_always_on = True

            if time_always_on:  # Time Always On
                if not device.is_on:
                    logger.debug(f"{device.name} is turning on | Always On")
                    await device.async_turn_on()

            elif device.solar_power_on and self.__sun.is_day():  # Solar-Energy Power On
                if not device.is_on and power_produced > device.current_power_usage:  # to On
                    logger.debug(f"{device.name} is turning on")
                    await device.async_turn_on()

                    power_produced -= device.current_power_usage

                elif device.is_on and (power_produced < 0 and now > device.next_power_status_change):  # to Off
                    logger.debug(f"{device.name} is turning off")
                    await device.async_turn_off()

                    instant_metrics = await device.async_get_instant_metrics()
                    if instant_metrics is not None:
                        power_produced += instant_metrics.power
                    else:
                        power_produced += device.current_power_usage

            elif device.is_on and now > device.next_power_status_change:  # Always Off
                logger.debug(f"{device.name} is turning off | Always Off")
                await device.async_turn_off()

    def get_device(self, device_id):
        return self.__manager.get_device(device_id)

    def unlock_device(self, device_id):
        device = self.__manager.get_device(device_id)
        if device is not None:
            device.unlock()
        else:
            logger.warning('No device found for %s', device_id)

    def lock_device(self, device_id, delay=None):
        device = self.__manager.get_device(device_id)
        if device is not None:
            if delay is not None:
                device.lock_for(delay)
            else:
                device.lock()
        else:
            logger.warning('No device found for %s', device_id)

    async def async_close(self):
        self.__scheduler.shutdown(wait=False)
        await self.__manager.async_stop()
        logger.debug('SERVICE STOPPED')
