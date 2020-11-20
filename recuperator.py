import asyncio
import pickledb
import datetime
import settings
import logging
from logging.handlers import SysLogHandler, RotatingFileHandler

from timer import RepeatedTimer
from gpiozero import Buzzer, TonalBuzzer, Button, DigitalInputDevice
import lcddriver
import psutil
import time
from uuid import getnode as get_mac

mac = get_mac()
uptime = lambda start=psutil.boot_time(): time.time() - start

log = logging.getLogger(__name__)
log.level = logging.DEBUG

formatter = logging.Formatter('%(module)s[%(process)d] %(funcName)s: [%(levelname)s] %(message)s')

sysloghandler = SysLogHandler(address = '/dev/log')
sysloghandler.formatter = formatter
sysloghandler.setLevel(logging.INFO)
log.addHandler(sysloghandler)

if(settings.LOG_FILE_NAME):
    filehandler = RotatingFileHandler(settings.LOG_FILE_NAME, maxBytes=settings.LOG_FILE_SIZE, backupCount=settings.LOG_BACK_COUNT)
    filehandler.formatter = formatter
    filehandler.setLevel(logging.DEBUG)
    log.addHandler(filehandler)

def exception_logger(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            log.exception(f'Error in {func} method', stack_info=True)
    return wrapper

buzzer = Buzzer(settings.BUZZER_PIN)
db = pickledb.load(settings.DATABASE_NAME, True)
display = lcddriver.lcd()

sensors = [
    DigitalInputDevice(settings.LAMP1_SENSOR_PIN),
    DigitalInputDevice(settings.LAMP2_SENSOR_PIN),
    DigitalInputDevice(settings.LAMP3_SENSOR_PIN)
]

buttons = [
    Button(settings.LAMP1_BUTTON_PIN, hold_time=settings.LAMP_BUTTON_HOLD_TIME),
    Button(settings.LAMP2_BUTTON_PIN, hold_time=settings.LAMP_BUTTON_HOLD_TIME),
    Button(settings.LAMP3_BUTTON_PIN, hold_time=settings.LAMP_BUTTON_HOLD_TIME)
]

errors = [False, False, False]

@exception_logger
def addSecs(date, secs):    
    result = date + datetime.timedelta(seconds=secs)    
    return result

@exception_logger
def reset_lamp_time(id):
    buzzer.beep(0.05, 0.05, 2)
    log.info(f'reset_lamp_time for id {id}')
    db.set(f'lamp{id}_error', False)
    db.set(f'lamp{id}_time', datetime.datetime.min.isoformat())

@exception_logger
def set_lamp_error(id):
    db.set(f'lamp{id + 1}_error', True)
    errors[id] = True
    buzzer.beep(0.5, 0.5, 10)

@exception_logger
def add_lamp_time(id):    
    date = datetime.datetime.min
    if db.exists(f'lamp{id}_time'):
        date = datetime.datetime.fromisoformat(db.get(f'lamp{id}_time'))
    date = addSecs(date, 1)
    db.set(f'lamp{id}_time', date.isoformat())    

@exception_logger
def sensor_callback():
    for idx, sensor in enumerate(sensors):
        if sensor.value == 1:
                set_lamp_error(idx)
        else:
            if errors[idx]:
                errors[idx] = False
                db.set(f'lamp{idx}_error', False)
            add_lamp_time(idx)

display_mac = False

@exception_logger
def display_callback():
    global display_mac
    display.lcd_clear()
    for idx, sens in enumerate(sensors):
        date = datetime.datetime.min
        if db.exists(f'lamp{idx}_time'):
            date = db.get(f'lamp{idx}_time')
            date = datetime.datetime.fromisoformat(date)
        delta = date - datetime.datetime.min
        hours = delta.seconds // 3600     
        error = 'OK'
        if db.exists(f'lamp{idx}_error'):
            if db.get(f'lamp{idx}_error'):
                error = 'ERROR'
        message = f'L{idx}: {delta.days}d {hours}h {error}'
        display.lcd_display_string(message, idx+1)

    if display_mac:
        display.lcd_display_string(f'SN: {mac:X}', 4)
    else:
        up_seconds = uptime()
        up_days = up_seconds // (60*60*24)
        up_hours = (up_seconds - up_days) // 3600
        up_minutes = (up_seconds - (up_hours * 3600)) // 60
        display.lcd_display_string(f'UP {int(up_days)}d {int(up_hours):02d}h {int(up_minutes):02d}m', 4)
    display_mac = not display_mac

sensor_timer = RepeatedTimer(1,sensor_callback)
display_timer = RepeatedTimer(settings.DISPLAY_UPDATE_TIME, display_callback)

@exception_logger
async def main():
    buzzer.beep(0.05, 0.05, 3)
    display.lcd_clear()
    sensor_timer.start()
    display_timer.start()

    for idx, btn in enumerate(buttons):
        btn.when_held = lambda: reset_lamp_time(idx)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.create_task(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        sensor_timer.stop()
        display_timer.stop()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
