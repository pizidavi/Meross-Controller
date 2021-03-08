import asyncio
from app.App import App


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    app = App(loop)

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print('')
    except Exception as e:
        print(f'Error: {e}')

    app.close()
