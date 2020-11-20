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

def addSecs(date, secs):
    result = datetime.datetime.min
    try:
        result = date + datetime.timedelta(seconds=secs)
    except:
        log.exception('Error in addSecs method', stack_info=True)
    return result

def reset_lamp_time(id):
    try:
        buzzer.beep(0.05, 0.05, 2)
        log.info(f'reset_lamp_time for id {id}')
        db.set(f'lamp{id}_error', False)
        db.set(f'lamp{id}_time', datetime.datetime.min.isoformat())
    except Exception:
        log.exception('Error in reset_lamp_time method', stack_info=True)


def set_lamp_error(id):
    try:
        db.set(f'lamp{id + 1}_error', True)
        errors[id] = True
        buzzer.beep(0.5, 0.5, 10)
    except Exception:
        log.exception('Error in set_lamp_error method', stack_info=True)

def add_lamp_time(id):
    try:
        date = datetime.datetime.min
        if db.exists(f'lamp{id}_time'):
            date = datetime.datetime.fromisoformat(db.get(f'lamp{id}_time'))
        date = addSecs(date, 1)
        db.set(f'lamp{id}_time', date.isoformat())
    except Exception:
        log.exception('Error in add_lamp_time method', stack_info=True)

def sensor_callback():
    try:
        for idx, sensor in enumerate(sensors):
            if sensor.value == 1:
                    set_lamp_error(idx)
            else:
                if errors[idx]:
                    errors[idx] = False
                    db.set(f'lamp{idx}_error', False)
                add_lamp_time(idx)
    except Exception:
        log.exception('Error in sensor_callback method', stack_info=True)

display_mac = False

def display_callback():
    global display_mac

    try:
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
    except Exception:
        log.exception('Error in display_callback method', stack_info=True)

sensor_timer = RepeatedTimer(1,sensor_callback)
display_timer = RepeatedTimer(settings.DISPLAY_UPDATE_TIME, display_callback)

async def main():
    try:
        buzzer.beep(0.05, 0.05, 3)
        display.lcd_clear()
        sensor_timer.start()
        display_timer.start()

        for idx, btn in enumerate(buttons):
            btn.when_held = lambda: reset_lamp_time(idx)
    except Exception:
        log.exception('Error in main method', stack_info=True)


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
