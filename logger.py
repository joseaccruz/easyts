import logging
from logging.handlers import SysLogHandler
import os
import sys


def prg_name():
    return os.path.basename(sys.argv[0]).replace(".py", "")


def create_log(tofile=False, file_level=1, file_name=None, toconsole=False, console_level=1, tosyslog=False, syslog_level=1, syslog_address='/dev/log'):
    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]

    logger = logging.getLogger(prg_name())
    logger.setLevel(logging.DEBUG)

    fmt_general = logging.Formatter('%(asctime)s - %(name)s - %(thread)d - %(threadName)s - %(levelname)s - %(message)s')
    fmt_syslog = logging.Formatter('%(name)s: %(threadName)s; %(levelname)s; %(message)s')

    # logs to a file
    if tofile:
        if os.path.isdir(os.path.dirname(file_name)):
            fh = logging.FileHandler(file_name)
            fh.setLevel(levels[file_level])
            fh.setFormatter(fmt_general)
            logger.addHandler(fh)
        else:
            sys.stderr.write("\nLog file directory '%s' not found.\nCan't continue. Quitting...\n\n" % (os.path.dirname(file_name)))
            quit()

    # logs to the console
    if toconsole:
        ch = logging.StreamHandler()
        ch.setLevel(levels[console_level])
        ch.setFormatter(fmt_general)
        logger.addHandler(ch)

    # logs to syslog
    if tosyslog:
        sh = SysLogHandler(address=syslog_address)
        sh.setLevel(levels[syslog_level])
        sh.setFormatter(fmt_syslog)
        logger.addHandler(sh)

    return logger


def get_log(log_name):
    return logging.getLogger("%s.%s" % (prg_name(), log_name))


def close_log():
    logging.shutdown()
