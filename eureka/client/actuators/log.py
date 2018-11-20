import logging
from typing import Dict

levels = [
    'OFF',
    'ERROR',
    'WARN',
    'INFO',
    'DEBUG'
]

levelMap = {
    logging.ERROR: 'ERROR',
    logging.WARNING: 'WARN',
    logging.INFO: 'INFO',
    logging.DEBUG: 'DEBUG',
    logging.NOTSET: 'OFF'
}

reverseMap = {
    'ERROR': logging.ERROR,
    'WARN': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'OFF': logging.NOTSET
}


class LogRetrievalException(Exception):
    pass


def _find_basefilename():
    """Finds the logger base filename(s) currently there is only one
    """
    log_file = None
    root = logging.getLogger()
    for h in root.__dict__['handlers']:
        if h.__class__.__name__ in ('TimedRotatingFileHandler','RotatingFileHandler','FileHandler'):
            log_file = h.baseFilename

    return log_file


def get_log() -> str:
    filename = _find_basefilename()
    if filename is None:
        return None
    with open(filename) as log:
        return log.read()


def _logger_config(name: str, logger: logging.Logger) -> Dict[str,Dict[str,str]]:
    return {
        name: {
            'configuredLevel': levelMap[logger.getEffectiveLevel()],
            'effectiveLevel': levelMap[logger.getEffectiveLevel()]
        }
    }


def get_loggers() -> Dict:
    # add levels and root logger
    loggers = {'levels':levels, 'loggers': {
        'ROOT' : {
            'configuredLevel': levelMap[logging.getLogger().getEffectiveLevel()],
            'effectiveLevel': levelMap[logging.getLogger().getEffectiveLevel()]
        }
    }}

    # get all configured loggers
    for name, logger in logging.Logger.manager.loggerDict.items():
        if hasattr(logger, 'getEffectiveLevel'):
            loggers['loggers'].update(_logger_config(name, logger))

    return loggers


def set_logger_level(logger: str, level: str):
    log = logging.getLogger(__name__)
    if logger == 'ROOT':
        log.debug('Setting level for root logger')
        logging.getLogger().setLevel(reverseMap[level])
        return

    if logger not in logging.Logger.manager.loggerDict:
        log.error(f'No logger {logger} is defined')
        raise LogRetrievalException(f'Could find logger {logger} is defined set of logs')

    log.debug('Returning logger from ')
    logging.Logger.manager.loggerDict[logger].setLevel(reverseMap[level])

