from control.Config import Config
from database.Database import Database

config = Config()


class DAO:

    def __init__(self):
        self.__db = Database(config.database.host,
                             config.database.user,
                             config.database.password,
                             config.database.database)

    def get_users(self):
        sql = "SELECT * " \
              "FROM users"
        result = self.__db.execute(sql)
        return result.fetchall()

    def search_user(self, telegram_from_id: str):
        sql = "SELECT * " \
              "FROM users " \
              "WHERE strIdTelegram = %s"
        result = self.__db.execute(sql, telegram_from_id)
        return result.fetchone()

    def get_all_devices(self):
        sql = "SELECT *, " \
                "(SELECT dtaDate " \
                "FROM logs l " \
                "WHERE l.intIdDevice = d.intIdDevice and boolState = 1 " \
                "ORDER BY dtaDate DESC " \
                "LIMIT 1) as dtaLastPowerOn " \
              "FROM devices d"
        result = self.__db.execute(sql)
        return result.fetchall()

    def get_devices(self):
        sql = "SELECT * " \
              "FROM devices " \
              "WHERE boolDisable = 0"
        result = self.__db.execute(sql)
        return result.fetchall()

    def get_device(self, device_id: int):
        sql = "SELECT * " \
              "FROM devices d " \
              "WHERE intIdDevice = %s"
        result = self.__db.execute(sql, device_id)
        return result.fetchone()

    def get_device_times_always_power_on(self, device_id: int):
        sql = "SELECT timePowerOn, timePowerOff " \
              "FROM timesalwayspoweron " \
              "WHERE intIdDevice = %s and boolDisable = 0"
        result = self.__db.execute(sql, device_id)
        return result.fetchall()

    def get_device_powers_on(self, device_id: int, date: str):
        date += '%'
        sql = "SELECT * " \
              "FROM logs " \
              "WHERE dtaDate LIKE %s and intIdDevice = %s"
        result = self.__db.execute(sql, date, device_id)
        return result.fetchall()

    def log(self, device_id: int, state: int):
        sql = "INSERT INTO logs (intIdDevice, boolState) VALUES (%s, %s)"
        self.__db.execute(sql, device_id, state)
        self.__db.commit()

    def close(self):
        self.__db.close()
