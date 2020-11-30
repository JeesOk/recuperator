import asyncio
import datetime
import settings
from mylog import log
from timer import RepeatedTimer
from button import MyButton
from gpiozero import Buzzer, DigitalInputDevice
import lcddriver
import utils
from sqlitedict import SqliteDict

current_pos = 0
num = 1
serial = datetime.date.today()
display_serial = True


def btn_next(btn):
    global current_pos
    global buttons
    global serial

    current_pos = current_pos + 1
    display_enter_serial()
    if current_pos == 4:
        db['serial'] = f"{serial.strftime('%Y%m%d')}{num:02d}"
        main()


def btn_up(btn):
    global serial
    global num

    if current_pos == 0:
        serial = utils.add_years(serial)
    if current_pos == 1:
        serial = utils.add_months(serial)
    if current_pos == 2:
        serial = utils.add_days(serial)
    if current_pos == 3:
        num = num + 1
    display_enter_serial()


def btn_down(btn):
    global serial
    global num

    if current_pos == 0:
        serial = utils.add_years(serial, -1)
    if current_pos == 1:
        serial = utils.add_months(serial, -1)
    if current_pos == 2:
        serial = utils.add_days(serial, -1)
    if current_pos == 3:
        num = num - 1

    display_enter_serial()


buzzer = Buzzer(settings.BUZZER_PIN)
db = SqliteDict(settings.DATABASE_NAME, tablename='values', autocommit=True)
display = lcddriver.lcd()

sensors = [
    DigitalInputDevice(settings.LAMP1_SENSOR_PIN),
    DigitalInputDevice(settings.LAMP2_SENSOR_PIN),
    DigitalInputDevice(settings.LAMP3_SENSOR_PIN)
]

errors = [False, False, False]


def reset_lamp_time(btn):
    id = btn.index
    buzzer.beep(0.05, 0.05, 2)
    log.info(f'reset_lamp_time for id {id}')
    db[f'lamp{id}_error'] = False
    errors[id] = False
    db[f'lamp{id}_time'] = datetime.datetime.min


def set_lamp_error(id):
    db[f'lamp{id}_error'] = True
    errors[id] = True
    buzzer.beep(0.5, 0.5, 10)


def add_lamp_time(id):
    date = datetime.datetime.min
    if f'lamp{id}_time' in db:
        date = db[f'lamp{id}_time']
    date = utils.add_seconds(date)
    db[f'lamp{id}_time'] = date


def sensor_callback():
    for idx, sensor in enumerate(sensors):
        if sensor.value == 1:
            if not errors[idx]:
                set_lamp_error(idx)

        if not errors[idx]:
            add_lamp_time(idx)


def display_callback():
    global display_serial
    display.lcd_clear()
    for idx, sens in enumerate(sensors):
        date = datetime.datetime.min
        if f'lamp{idx}_time' in db:
            date = db[f'lamp{idx}_time']
        delta = date - datetime.datetime.min
        hours = delta.seconds // 3600
        mins = (delta.seconds - (hours * 3600)) // 60
        error = 'OK'
        if f'lamp{idx}_error' in db:
            if db[f'lamp{idx}_error']:
                error = 'ER'
        message = f'L{idx}: {delta.days:>3d}d {hours:>2d}h {mins:>2d}m {error}'
        display.lcd_display_string(message, idx + 1)

    if display_serial:
        display.lcd_display_string(f'SN: {serial}', 4)
    else:
        up_seconds = utils.uptime()
        up_days = up_seconds // 86400
        up_hours = (up_seconds - (up_days * 86400)) // 3600
        up_minutes = (up_seconds - (up_hours * 3600) - (up_days * 86400)) // 60
        display.lcd_display_string(f'UP: {int(up_days):>3d}d {int(up_hours):>2d}h {int(up_minutes):>2d}m', 4)
    display_serial = not display_serial


sensor_timer = RepeatedTimer(1, sensor_callback)
display_timer = RepeatedTimer(settings.DISPLAY_UPDATE_TIME, display_callback)

buttons = [
    MyButton(settings.LAMP1_BUTTON_PIN, reset_lamp_time, btn_next, 0),
    MyButton(settings.LAMP2_BUTTON_PIN, reset_lamp_time, btn_up, 1),
    MyButton(settings.LAMP3_BUTTON_PIN, reset_lamp_time, btn_down, 2)
]


def display_enter_serial():
    display.lcd_clear()
    display.lcd_display_string('Enter serial', 1)
    if current_pos == 0:
        display.lcd_display_string('____', 2)
    if current_pos == 1:
        display.lcd_display_string('    __', 2)
    if current_pos == 2:
        display.lcd_display_string('      __', 2)
    if current_pos == 3:
        display.lcd_display_string('        __', 2)
    display.lcd_display_string(f"{serial.strftime('%Y%m%d')}{num:02d}", 3)


async def enter_serial():
    display_enter_serial()


def main():
    global serial
    buzzer.beep(0.05, 0.05, 3)
    log.info('=== Application started ===')
    display.lcd_clear()
    serial = f"{serial.strftime('%Y%m%d')}{num:02d}"
    sensor_timer.start()
    display_timer.start()

    for idx, btn in enumerate(buttons):
        btn.pressed = None

    for idx, sensor in enumerate(sensors):
        key = f'lamp{id}_error'
        if key in db:
            errors[idx] = db[key]


async def main_task():
    main()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if ('serial' in db) and (not db['serial'] is None):
            loop.create_task(main_task())
        else:
            loop.create_task(enter_serial())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        sensor_timer.stop()
        display_timer.stop()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
