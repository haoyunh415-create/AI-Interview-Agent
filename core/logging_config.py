import logging
import sys
import time

_loggers = {}


def setup_logging(level=logging.INFO):
    root = logging.getLogger("tech-chat")
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s - %(message)s",
        datefmt="%m-%d %H:%M:%S",
    ))
    root.addHandler(handler)
    root.propagate = False
    return root


def get_logger(name=None):
    if name:
        full = f"tech-chat.{name}"
    else:
        full = "tech-chat"

    if full not in _loggers:
        _loggers[full] = logging.getLogger(full)

    return _loggers[full]


def log_duration(logger, label, start_time):
    elapsed = (time.monotonic() - start_time) * 1000
    logger.info("%s completed in %.0fms", label, elapsed)


setup_logging()
