from datetime import datetime, timedelta

from control.DAO import DAO

# Variables
dao = DAO()


# Functions
def get_devices():
    response = []

    devices = dao.get_all_devices()
    for row in devices:
        device_id = row.intIdDevice

        times = []
        for _row in dao.get_device_times_always_power_on(device_id):
            times.append({
                'start': (datetime.fromtimestamp(_row.timePowerOn.seconds) - timedelta(hours=1)).time(),
                'end': (datetime.fromtimestamp(_row.timePowerOff.seconds) - timedelta(hours=1)).time()
            })

        response.append({
            'id': device_id,
            'name': row.strName,
            'currentPowerUsage': row.intUsage,
            'solarPowerOn': bool(row.boolSolarPowerOn),
            'timeDelayBeforePowerOff': row.timeDelayBeforePowerOff,
            'timesAlwaysOn': times,
            'lastPowerOn': row.dtaLastPowerOn,
            'disabled': bool(row.boolDisable)
        })
    return response


async def log(device, state):
    dao.log(device, state)
