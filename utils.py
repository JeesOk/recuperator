from dateutil.relativedelta import relativedelta
# import psutil
import time


def add_years(d, years=1):
    return d + relativedelta(years=years)


def add_months(d, months=1):
    return d + relativedelta(months=months)


def add_days(d, days=1):
    return d + relativedelta(days=days)


def add_hours(d, hours=1):
    return d + relativedelta(hours=hours)


def add_minutes(d, minutes=1):
    return d + relativedelta(minutes=minutes)


def add_seconds(d, seconds=1):
    return d + relativedelta(seconds=seconds)


# uptime = lambda start=psutil.boot_time(): time.time() - start


# def exception_logger(func, log):
#    def wrapper(*args, **kwargs):
#        try:
#            return func(*args, **kwargs)
#        except Exception:
#            log.exception(f'Error in {func} method', stack_info=True)
#
#    return wrapper
