import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import lib.Logging as Log
from lib.Config import Config
from control.Meross import Meross
from lib.SolarEdge import SolarEdge

# Logging
logging.getLogger('meross_iot').setLevel(logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

logger = Log.get_logger(__name__)
config = Config()


class MerossController:

    def __init__(self, loop=None):
        self.__loop = asyncio.get_event_loop() if loop is None else loop

        self.__manager = Meross(config.meross.email, config.meross.password)
        self.__solaredge = SolarEdge(config.solaredge.api_token, config.solaredge.site_id)

        self.__scheduler = AsyncIOScheduler()
        self.__scheduler.add_job(self.__async_loop, 'interval', minutes=5)

        self.__loop.run_until_complete(self.async_init())

    async def async_init(self):
        logger.info('MerossController started')
        await self.__manager.async_init()
        self.__scheduler.start()

    async def __async_loop(self):
        now = datetime.now()

        devices = self.__manager.find_devices()
        if not len(devices):
            return

        result = self.__solaredge.get_current_power_flow(sunrise=config.sun.sunrise, sunset=config.sun.sunset)
        power_produced = (result['PV'] - result['LOAD']) if result else -config.solaredge.home_default_load
        logger.info(f"Remaining power: {power_produced} W")

        for device in devices:
            await device.async_update()  # Update device information

            time_always_on = False
            for time in device.times_always_on:
                if time['start'] <= now.time() < time['end']:  # Check All Times Always On
                    time_always_on = True

            if time_always_on:  # Time Always On
                if not device.is_on:
                    logger.debug(f"{device.name} is turning on | Always On")
                    await device.async_turn_on()

            elif device.solar_power_on and \
                    (config.sun.sunrise <= now.time() < config.sun.sunset or device.is_on):  # Solar-Energy Power On
                if not device.is_on and power_produced > device.current_power_usage:  # to On
                    logger.debug(f"{device.name} is turning on")
                    await device.async_turn_on()

                    power_produced -= device.current_power_usage

                elif device.is_on and (power_produced < 0 and now > device.next_power_status_change):  # to Off
                    logger.debug(f"{device.name} is turning off")
                    await device.async_turn_off()

                    power_produced += device.current_power_usage

            elif device.is_on and now > device.next_power_status_change:  # Always Off
                logger.debug(f"{device.name} is turning off | Always Off")
                await device.async_turn_off()

    def close(self):
        self.__loop.run_until_complete(self.async_close())

    async def async_close(self):
        self.__scheduler.shutdown(wait=False)
        await self.__manager.async_stop()
        logger.debug('SERVICE STOPPED')
