import threading
from datetime import datetime, timedelta


class Timer(threading.Timer):

    def __init__(self, interval, function, args=None, kwargs=None):
        super().__init__(interval, function, args, kwargs)
        self.__interval = timedelta(seconds=interval)
        self.__started_at = None

    @property
    def started_at(self) -> datetime or None:
        return self.__started_at

    @property
    def expire_at(self) -> datetime or None:
        if self.started_at is not None:
            return self.started_at + self.__interval
        return None

    @property
    def elapsed(self) -> timedelta or None:
        if self.started_at is not None:
            return datetime.now() - self.started_at
        return None

    @property
    def remaining(self) -> timedelta or None:
        if self.started_at is not None:
            return self.__interval - self.elapsed
        return None

    def start(self):
        super().start()
        self.__started_at = datetime.now()

    def cancel(self):
        super().cancel()
        self.__started_at = None
