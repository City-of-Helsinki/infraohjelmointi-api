from io import StringIO
import logging
from django.test import SimpleTestCase
from project.extensions.ColoredFormatter import ColoredFormatter

class ColoredFormatterTestCase(SimpleTestCase):
    def setUp(self):
        self.defaultErrorMessage = "Logging message has incorrect"
        self.logger = logging.getLogger("infraohjelmointi_api_test")
        self.logger.setLevel(logging.DEBUG)
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.formatter = ColoredFormatter("%(levelname)s: %(message)s")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        self.logger.removeHandler(self.handler)

    def create_log_record(self, level, message):
        return logging.LogRecord(
            name="test",
            level=level,
            pathname=__file__,
            lineno=10,
            msg=message,
            args=(),
            exc_info=None,
            func=None,
            sinfo=None
        )

    """
    Debug message test
    """
    def test_formatting_debug(self):
        record = self.create_log_record(logging.DEBUG, "This is a debug message.")
        formatted = self.formatter.format(record)
        self.assertIn(
            '\033[38;2;255;153;0m',
            formatted,
            f"{self.defaultErrorMessage} formatting: {formatted}"
        )
        self.assertIn(
            'DEBUG: This is a debug message.',
            formatted,
            f"{self.defaultErrorMessage} message: {formatted}"
        )

    """
    Info message test
    """
    def test_formatting_info(self):
        record = self.create_log_record(logging.INFO, "This is an info message.")
        formatted = self.formatter.format(record)
        self.assertIn(
            '\033[38;2;102;255;102m',
            formatted,
            f"{self.defaultErrorMessage} formatting: {formatted}"
        )
        self.assertIn(
            'INFO: This is an info message.',
            formatted,
            f"{self.defaultErrorMessage} message: {formatted}"
        )

    """
    Warning message test
    """
    def test_formatting_warning(self):
        record = self.create_log_record(logging.WARNING, "This is a warning message.")
        formatted = self.formatter.format(record)
        self.assertIn(
            '\033[38;2;255;255;204m',
            formatted,
            f"{self.defaultErrorMessage} formatting: {formatted}"
        )
        self.assertIn(
            'WARNING: This is a warning message.',
            formatted,
            f"{self.defaultErrorMessage} message: {formatted}"
        )

    """
    Error message test
    """
    def test_formatting_error(self):
        record = self.create_log_record(logging.ERROR, "This is an error message.")
        formatted = self.formatter.format(record)
        self.assertIn(
            '\033[38;2;255;51;0m',
            formatted,
            f"{self.defaultErrorMessage} formatting: {formatted}"
        )
        self.assertIn(
            'ERROR: This is an error message.',
            formatted,
            f"{self.defaultErrorMessage} message: {formatted}"
        )

    """
    Critical message test
    """
    def test_formatting_critical(self):
        record = self.create_log_record(logging.CRITICAL, "This is a critical message.")
        formatted = self.formatter.format(record)
        self.assertIn(
            '\033[38;2;255;0;0m',
            formatted,
            f"{self.defaultErrorMessage} formatting: {formatted}"
        )
        self.assertIn(
            'CRITICAL: This is a critical message.',
            formatted,
            f"{self.defaultErrorMessage} message: {formatted}"
        )
