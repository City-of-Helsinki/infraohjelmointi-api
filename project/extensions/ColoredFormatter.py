import logging


class ColoredFormatter(logging.Formatter):
    def __init__(
        self, format=None, datefmt=None, style="%", validate=True, *, defaults=None
    ):
        super().__init__(
            fmt=format,
            datefmt=datefmt,
            style=style,
            validate=validate,
            defaults=defaults,
        )
        self.fmt = format
        self.FORMATS = {
            logging.DEBUG: f"\033[38;2;255;153;0m{self.fmt}\033[0m",
            logging.INFO: f"\033[38;2;102;255;102m{self.fmt}\033[0m",
            logging.WARNING: f"\033[38;2;255;255;204m{self.fmt}\033[0m",
            logging.ERROR: f"\033[38;2;255;51;0m{self.fmt}\033[0m",
            logging.CRITICAL: f"\033[38;2;255;0;0m{self.fmt}\033[0m",
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
