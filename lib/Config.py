import json
import math
from datetime import datetime, time

import lib.Logging as Log

logger = Log.get_logger(__name__)
FILENAME = 'config.json'


class Config:

    class __MerossConfig:

        def __init__(self, config):
            self.__email = config['email']
            self.__password = config['password']

        email = property(lambda self: self.__email)
        password = property(lambda self: self.__password)

    class __SolarEdgeConfig:

        def __init__(self, config):
            self.__api_token = config['api_token']
            self.__site_id = config['site_id']
            self.__home_default_load = config['home_default_load']

        api_token = property(lambda self: self.__api_token)
        site_id = property(lambda self: self.__site_id)
        home_default_load = property(lambda self: self.__home_default_load)

    class __Sun:

        class SunTimeException(Exception):
            pass

        __SUNRISE = 'rise'
        __SUNSET = 'set'

        def __init__(self, config):
            self.__latitude = config['latitude']
            self.__longitude = config['longitude']
            self.__timezone = config['timezone']

        sunrise = property(lambda self: self.__calc(self.__SUNRISE))
        sunset = property(lambda self: self.__calc(self.__SUNSET))

        def __calc(self, what, zenith=90.8) -> time:
            """
            :param what: __SUNRISE -> sunrise;
                         __SUNSET  -> sunset
            :return: time
            """
            def get_current_utc():
                now = datetime.now()
                return [now.day, now.month, now.year]

            def force_range(v, maximum):
                if v < 0:
                    return v + maximum
                elif v >= maximum:
                    return v - maximum
                return v

            day, month, year = get_current_utc()

            latitude = self.__latitude
            longitude = self.__longitude
            timezone = self.__timezone

            TO_RAD = math.pi / 180

            # 1. first calculate the day of the year
            N1 = math.floor(275 * month / 9)
            N2 = math.floor((month + 9) / 12)
            N3 = (1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3))
            N = N1 - (N2 * N3) + day - 30

            # 2. convert the longitude to hour value and calculate an approximate time
            lngHour = longitude / 15

            if what == self.__SUNRISE:
                t = N + ((6 - lngHour) / 24)
            else:  # sunset
                t = N + ((18 - lngHour) / 24)

            # 3. calculate the Sun's mean anomaly
            M = (0.9856 * t) - 3.289

            # 4. calculate the Sun's true longitude
            L = M + (1.916 * math.sin(TO_RAD * M)) + (0.020 * math.sin(TO_RAD * 2 * M)) + 282.634
            L = force_range(L, 360)  # NOTE: L adjusted into the range [0,360)

            # 5a. calculate the Sun's right ascension

            RA = (1 / TO_RAD) * math.atan(0.91764 * math.tan(TO_RAD * L))
            RA = force_range(RA, 360)  # NOTE: RA adjusted into the range [0,360)

            # 5b. right ascension value needs to be in the same quadrant as L
            Lquadrant = (math.floor(L / 90)) * 90
            RAquadrant = (math.floor(RA / 90)) * 90
            RA = RA + (Lquadrant - RAquadrant)

            # 5c. right ascension value needs to be converted into hours
            RA = RA / 15

            # 6. calculate the Sun's declination
            sinDec = 0.39782 * math.sin(TO_RAD * L)
            cosDec = math.cos(math.asin(sinDec))

            # 7a. calculate the Sun's local hour angle
            cosH = (math.cos(TO_RAD * zenith) - (sinDec * math.sin(TO_RAD * latitude))) / (
                        cosDec * math.cos(TO_RAD * latitude))

            if cosH > 1:
                raise self.SunTimeException('The sun never rises on this location (on the specified date)')
            if cosH < -1:
                raise self.SunTimeException('The sun never sets on this location (on the specified date)')

            # 7b. finish calculating H and convert into hours
            if what == self.__SUNRISE:
                H = 360 - (1 / TO_RAD) * math.acos(cosH)
            else:
                H = (1 / TO_RAD) * math.acos(cosH)

            H = H / 15

            # 8. calculate local mean time of rising/setting
            T = H + RA - (0.06571 * t) - 6.622

            # 9. adjust back to UTC
            UT = T - lngHour + timezone
            UT = force_range(UT, 24)  # UTC time in decimal format (e.g. 23.23)

            # 10. Return
            hour = int(UT)
            minute = int((UT * 60) % 60)
            second = 0

            return time(hour=hour, minute=minute, second=second)

    class __TelegramConfig:

        def __init__(self, config):
            self.__token = config['token']

        token = property(lambda self: self.__token)

    class __DatabaseConfig:

        def __init__(self, config):
            self.__host = config['host']
            self.__user = config['user']
            self.__password = config['password']
            self.__database = config['database']

        host = property(lambda self: self.__host)
        user = property(lambda self: self.__user)
        password = property(lambda self: self.__password)
        database = property(lambda self: self.__database)

    def __init__(self):
        file = open(FILENAME, 'r')
        self.__config = json.loads(file.read())

        self.__meross = self.__MerossConfig(self.__config['MEROSS'])
        self.__solaredge = self.__SolarEdgeConfig(self.__config['SOLAREDGE'])
        self.__sun = self.__Sun(self.__config['LOCATION'])
        self.__telegram = self.__TelegramConfig(self.__config['TELEGRAM'])
        self.__database = self.__DatabaseConfig(self.__config['DATABASE'])

        file.close()

    meross = property(lambda self: self.__meross)
    solaredge = property(lambda self: self.__solaredge)
    sun = property(lambda self: self.__sun)
    telegram = property(lambda self: self.__telegram)
    database = property(lambda self: self.__database)
