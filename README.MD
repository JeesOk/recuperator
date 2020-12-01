# RECUPERATOR LAMP

```bash
sudo apt install python3-gpiozero python3-smbus python3-pip
sudo pip3 install python-dateutil
sudo pip3 install psutil

sudo cp recuperator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable recuperator
sudo systemctl start recuperator
```

### settings

```python
LAMP1_SENSOR_PIN = 10  # SL1 *
LAMP2_SENSOR_PIN = 9   # SL2 +
LAMP3_SENSOR_PIN = 11  # SL3 -

LAMP1_BUTTON_PIN = 16  # ResL1
LAMP2_BUTTON_PIN = 20  # ResL2
LAMP3_BUTTON_PIN = 21  # ResL3

LAMP_BUTTON_HOLD_TIME = 3

DATABASE_NAME = 'recuperator.db.sqlite'

BUZZER_PIN = 23

DISPLAY_UPDATE_TIME = 1

LOG_FILE_NAME = 'recuperator.log'
LOG_FILE_SIZE = 1048576
LOG_BACK_COUNT = 10
```