import logging
from logging.handlers import SysLogHandler, RotatingFileHandler
import settings


log = logging.getLogger(__name__)
log.level = logging.DEBUG

formatter = logging.Formatter('%(module)s[%(process)d] %(funcName)s: [%(levelname)s] %(message)s')

sysloghandler = SysLogHandler(address='/dev/log')
sysloghandler.formatter = formatter
sysloghandler.setLevel(logging.INFO)
log.addHandler(sysloghandler)

if settings.LOG_FILE_NAME:
    filehandler = RotatingFileHandler(settings.LOG_FILE_NAME, maxBytes=settings.LOG_FILE_SIZE, backupCount=settings.LOG_BACK_COUNT)
    filehandler.formatter = formatter
    filehandler.setLevel(logging.DEBUG)
    log.addHandler(filehandler)