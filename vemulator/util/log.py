import logging

import colorlog

debugging = True
stdout_logging = False


def set_stdout_logging(enabled):
    """
    Enable stdout logging instead of only logging to files
    NOTE: This function must be called before init_logger!
    :param enabled: True to log to stdout and files, False to only log to files (default)
    :type enabled: bool
    """
    global stdout_logging
    stdout_logging = enabled

def set_debugging(enabled):
    """
    Enable logging debug information.
    NOTE: This function must be called before init_logger!
    :param debugging: True to log debugging information, False to not log debugging information.
    :type debugging: bool
    """
    global debugging
    debugging = enabled


def init_logger(module_name) -> logging.Logger:
    """
    Initialize the logger
    :param module_name: name of the module writing to the log
    :type module_name: str
    :return: logger
    :rtype logging.Logger
    """
    log_format = (
        '%(asctime)s - '
        '%(name)s - '
        '%(funcName)s - '
        '%(levelname)s - '
        '%(message)s'
    )

    if stdout_logging:
        colorlog.basicConfig(format=f'\033[1m %(log_color)s {log_format}', log_colors={
            'DEBUG': 'white',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
            'EMULATION': 'yellow'})

    logging.addLevelName(15, 'EMULATION')
    logger = logging.getLogger(module_name)

    if debugging:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    fh = logging.FileHandler('app.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    fh = logging.FileHandler('app.warning.log')
    fh.setLevel(logging.WARNING)
    formatter = logging.Formatter(log_format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    fh = logging.FileHandler('app.error.log')
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter(log_format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger
