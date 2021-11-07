import urllib3
import certifi
import json
from datetime import datetime, time


class SolarEdge:

    __WEBSITE = 'https://monitoringapi.solaredge.com/site/{site_id}/{action}.json?api_key={api_token}'
    __METHOD = 'GET'

    def __init__(self, api_token: str, site_id: int or str, home_default_load: int):
        self.__request = urllib3.PoolManager(ca_certs=certifi.where())

        self.__api_token = api_token
        self.__site_id = site_id
        self.__home_default_load = home_default_load

    def get_current_power_flow(self, sunrise: time, sunset: time) -> dict or None:
        """
        :param sunrise: time | Sunrise hour
        :param sunset:  time | Sunset hour
        :return: dict or None
        """
        now = datetime.now()
        unit = 'W'

        if sunrise <= now.time() < sunset:
            data = self.__execute('currentPowerFlow')
            if not data:
                return None

            data = data['siteCurrentPowerFlow']

            pv = int(data['PV']['currentPower'] * (1000 if data['unit'] == 'kW' else 1)) if 'PV' in data else None
            load = int(data['LOAD']['currentPower'] * (1000 if data['unit'] == 'kW' else 1))
            grid = int(data['GRID']['currentPower'] * (1000 if data['unit'] == 'kW' else 1))

            return {
                'PV': pv,
                'LOAD': load,
                'GRID': grid,
                'unit': unit
            }
        else:
            return {
                'PV': 0,
                'LOAD': self.__home_default_load,
                'GRID': self.__home_default_load,
                'unit': unit
            }

    def __execute(self, action: str):
        url = self.__WEBSITE.format(site_id=self.__site_id, action=action, api_token=self.__api_token)
        result = self.__request.request(self.__METHOD, url)
        return json.loads(result.data) if result.status == 200 else None
