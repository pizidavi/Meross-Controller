import mysql.connector


class Database:

    def __init__(self, host, user, password, database):
        self.__db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8',
            autocommit=True
        )
        self.__cursor = self.__db.cursor(named_tuple=True)

    def execute(self, sql, *args):
        self.__cursor.execute(sql, args)
        return self.__cursor

    def commit(self):
        self.__db.commit()

    def close(self):
        self.__cursor.close()
        self.__db.close()

    __del__ = close
