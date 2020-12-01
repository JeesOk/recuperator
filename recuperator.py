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
serial_num = 1
serial_date = datetime.date.today()


def btn_next(btn):
    global current_pos
    global serial_date
    global serial_num

    current_pos = current_pos + 1
    display_enter_serial()
    if current_pos == 4:
        db['serial_date'] = serial_date
        db['serial_num'] = serial_num
        main()


def btn_up(btn):
    global serial_date
    global serial_num

    if current_pos == 0:
        serial_date = utils.add_years(serial_date)
    if current_pos == 1:
        serial_date = utils.add_months(serial_date)
    if current_pos == 2:
        serial_date = utils.add_days(serial_date)
    if current_pos == 3:
        serial_num = serial_num + 1
    display_enter_serial()


def btn_down(btn):
    global serial_date
    global serial_num

    if current_pos == 0:
        serial_date = utils.add_years(serial_date, -1)
    if current_pos == 1:
        serial_date = utils.add_months(serial_date, -1)
    if current_pos == 2:
        serial_date = utils.add_days(serial_date, -1)
    if current_pos == 3:
        serial_num = serial_num - 1

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
    idx = btn.index
    buzzer.beep(0.05, 0.05, 2)
    log.info(f'reset_lamp_time for id {idx}')
    db[f'lamp{idx}_error'] = False
    errors[idx] = False
    db[f'lamp{idx}_time'] = datetime.datetime.min


def set_lamp_error(idx):
    log.warning(f'Lamp {idx} error')
    db[f'lamp{idx}_error'] = True
    errors[idx] = True
    buzzer.beep(0.5, 0.5, 10)


def add_lamp_time(idx):
    date = datetime.datetime.min
    key = f'lamp{idx}_time'
    if key in db:
        date = db[key]
    date = utils.add_seconds(date)
    db[key] = date


def sensor_callback():
    for idx, sensor in enumerate(sensors):
        if sensor.value == 1:
            if not errors[idx]:
                set_lamp_error(idx)

        if not errors[idx]:
            add_lamp_time(idx)


def display_callback():
    # display.lcd_clear()
    for idx, sens in enumerate(sensors):
        date = datetime.datetime.min
        if f'lamp{idx}_time' in db:
            date = db[f'lamp{idx}_time']
        delta = date - datetime.datetime.min
        hours = delta.seconds // 3600
        minutes = (delta.seconds - (hours * 3600)) // 60
        error = 'OK'
        if f'lamp{idx}_error' in db:
            if db[f'lamp{idx}_error']:
                error = 'ER'
        message = f'L{idx+1}: {delta.days:>3d}d {hours:>2d}h {minutes:>2d}m {error}'
        message = f'{message:<20}'
        display.lcd_display_string(message, idx + 1)

    message = f"SN: {serial_date.strftime('%Y%m%d')}{serial_num:02d}"
    message = f'{message:<20}'
    display.lcd_display_string(message, 4)


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
    message = ''
    if current_pos == 0:
        message = '____'
    if current_pos == 1:
        message = '{:>6}'.format('__')
    if current_pos == 2:
        message = '{:>8}'.format('__')
    if current_pos == 3:
        message = '{:>10}'.format('__')
    display.lcd_display_string(f'{message:<20}', 2)
    display.lcd_display_string(f"{serial_date.strftime('%Y%m%d')}{serial_num:02d}", 3)


async def enter_serial():
    display_enter_serial()


def main():
    global serial_date
    global serial_num

    buzzer.beep(0.05, 0.05, 3)
    log.info('=== Application started ===')
    display.lcd_clear()
    # serial = f"{serial.strftime('%Y%m%d')}{num:02d}"
    serial_date = db['serial_date']
    serial_num = db['serial_num']
    log.info(f'Stored serial: {serial_date.strftime("%Y%m%d")}{serial_num:02d}')

    sensor_timer.start()
    display_timer.start()

    for idx, btn in enumerate(buttons):
        btn.pressed = None

    for idx, sensor in enumerate(sensors):
        key = f'lamp{idx}_error'
        if key in db:
            errors[idx] = db[key]
            if errors[idx]:
                log.info(f'For lamp {idx} stored error')


async def main_task():
    main()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if (('serial_date' in db) and (not db['serial_date'] is None)) and (('serial_num' in db) and (not db['serial_num'] is None)):
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
