# Imports
import asyncio
from app.MerossController import MerossController
from app.TelegramBot import TelegramBot


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    controller = MerossController(loop)
    bot = TelegramBot()

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("")
    except Exception as e:
        print(f'Error: {e}')

    controller.close()
    bot.close()

    # loop.close()
