import time
import asyncio
from datetime import datetime

from app.App import App


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    timeout_minutes = 5
    current_time = datetime.now()
    wait_time = timeout_minutes * 60 - (current_time.minute % timeout_minutes)*60 - current_time.second
    time.sleep(wait_time)

    app = App(loop)

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print('')
    except Exception as e:
        print(f'Error: {e}')

    app.close()
