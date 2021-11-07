import json

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

        def __init__(self, config):
            self.__latitude = config['latitude']
            self.__longitude = config['longitude']
            self.__timezone = config['timezone']

        latitude = property(lambda self: self.__latitude)
        longitude = property(lambda self: self.__longitude)
        timezone = property(lambda self: self.__timezone)

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
