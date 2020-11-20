import asyncio
import pickledb
import datetime
import settings
import logging as log
from timer import RepeatedTimer
from gpiozero import Buzzer, TonalBuzzer, Button, DigitalInputDevice
import lcddriver

log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(message)s') 

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
    result = date + datetime.timedelta(seconds=secs)
    return result

def reset_lamp_time(id):
    buzzer.beep(0.05, 0.05, 2)
    log.info(f'reset_lamp_time for id {id}')
    db.set(f'lamp{idx}_error', False)
    db.set(f'lamp{idx}_time', datetime.datetime.min)


def set_lamp_error(id):
    db.set(f'lamp{id + 1}_error', True)
    errors[id] = True
    buzzer.beep(0.5, 0.5, 10)

def add_lamp_time(id):
    date = datetime.datetime.min
    if db.exists(f'lamp{id}_time'):
        date = datetime.datetime.fromisoformat(db.get(f'lamp{id}_time'))        
    date = addSecs(date, 1)
    db.set(f'lamp{idx}_time', date.isoformat())

def sensor_callback():
    for idx, sensor in enumerate(sensors):
        if sensor.value == 1:
                set_lamp_error(idx)
        else:                
            if errors[idx]:
                errors[idx] = False
                db.set(f'lamp{idx}_error', False)
            add_lamp_time(idx)

def display_callback():
    for idx, sens in enumerate(sensors):        
        if db.exists(f'lamp{idx}_time'):
            date = db.get(f'lamp{idx}_time')
            date = datetime.datetime.fromisoformat(date)
            delta = date - datetime.datetime.min
            hours = delta.seconds // 3600            
            display.print(f'L{idx}: {delta.days}d {hours}h', display.LCD_LINES[idx])

sensor_timer = RepeatedTimer(1,sensor_callback)
display_timer = RepeatedTimer(10, display_callback)

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
