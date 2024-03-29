import math
import time as tm
from datetime import datetime, date, time


class SunTimeException(Exception):
    pass


class Sun:

    __SUNRISE = 'rise'
    __SUNSET = 'set'

    def __init__(self, latitude: float, longitude: float, timezone: int):
        self.__latitude = latitude
        self.__longitude = longitude
        self.__timezone = timezone

        self.__sunrise = None
        self.__sunset = None
        self.__last_calc_sunrise = None
        self.__last_calc_sunset = None

    @property
    def sunrise(self) -> time:
        if self.__sunrise is None or self.__last_calc_sunrise != date.today():
            self.__sunrise = self.__calc(self.__SUNRISE)
            self.__last_calc_sunrise = date.today()
        return self.__sunrise

    @property
    def sunset(self) -> time:
        if self.__sunset is None or self.__last_calc_sunset != date.today():
            self.__sunset = self.__calc(self.__SUNSET)
            self.__last_calc_sunset = date.today()
        return self.__sunset

    def is_day(self, _time: time = None) -> bool:
        _time = _time if _time is not None else datetime.now().time()
        return self.sunrise <= _time < self.sunset

    def __calc(self, what, zenith=90.8) -> time:
        """
        :param what: __SUNRISE -> sunrise;
                     __SUNSET  -> sunset
        :return: time
        """

        def get_current_utc():
            dt = datetime.now()
            return [dt.day, dt.month, dt.year]

        def is_dst():
            return tm.localtime().tm_isdst

        def force_range(v, maximum):
            if v < 0:
                return v + maximum
            elif v >= maximum:
                return v - maximum
            return v

        day, month, year = get_current_utc()

        latitude = self.__latitude
        longitude = self.__longitude

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
            raise SunTimeException('The sun never rises on this location (on the specified date)')
        if cosH < -1:
            raise SunTimeException('The sun never sets on this location (on the specified date)')

        # 7b. finish calculating H and convert into hours
        if what == self.__SUNRISE:
            H = 360 - (1 / TO_RAD) * math.acos(cosH)
        else:
            H = (1 / TO_RAD) * math.acos(cosH)
        H /= 15

        # 8. calculate local mean time of rising/setting
        T = H + RA - (0.06571 * t) - 6.622

        # 9. adjust back to Local Time
        UT = T - lngHour + self.__timezone + int(is_dst())
        UT = force_range(UT, 24)  # UTC time in decimal format (e.g. 23.23)

        # 10. Return
        hour = int(UT)
        minute = int((UT * 60) % 60)
        return time(hour=hour, minute=minute)
