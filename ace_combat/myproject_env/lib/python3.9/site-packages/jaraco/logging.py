import os
import logging
import time
import datetime
import string
import http.client

import tempora


def log_level(level_string):
    """
    Return a log level for a string

    >>> log_level('DEBUG') == logging.DEBUG
    True
    >>> log_level('30') == logging.WARNING
    True
    """
    if level_string.isdigit():
        return int(level_string)
    return getattr(logging, level_string.upper())


def add_arguments(parser, default_level=logging.INFO):
    """
    Add arguments to an ArgumentParser or OptionParser for purposes of
    grabbing a logging level.

    >>> import argparse
    >>> add_arguments(argparse.ArgumentParser())
    """
    adder = getattr(parser, 'add_argument', None) or getattr(parser, 'add_option')
    adder(
        '-l',
        '--log-level',
        default=default_level,
        type=log_level,
        help="Set log level (DEBUG, INFO, WARNING, ERROR)",
    )


def setup(options, **kwargs):
    """
    Setup logging with options or arguments from an OptionParser or
    ArgumentParser. Also pass any keyword arguments to the basicConfig
    call.

    >>> import argparse
    >>> parser = argparse.ArgumentParser()
    >>> add_arguments(parser)
    >>> monkeypatch = getfixture('monkeypatch')
    >>> monkeypatch.setattr(logging, 'basicConfig', lambda **kwargs: print(kwargs))
    >>> setup(parser.parse_args([]))
    {'level': 20}
    """
    params = dict(kwargs)
    params.update(level=options.log_level)
    logging.basicConfig(**params)


def setup_requests_logging(level):
    """
    Setup logging for 'requests' such that it logs details about the
    connection, headers, etc.

    >>> monkeypatch = getfixture('monkeypatch')
    >>> monkeypatch.setattr(http.client.HTTPConnection, 'debuglevel', None)
    >>> setup_requests_logging(logging.DEBUG)
    >>> http.client.HTTPConnection.debuglevel
    True
    """
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(level)
    requests_log.propagate = True

    # enable debugging at httplib level
    http.client.HTTPConnection.debuglevel = level <= logging.DEBUG


class TimestampFileHandler(logging.StreamHandler):
    """
    A logging handler which will log to a file, similar to
    logging.handlers.RotatingFileHandler, but instead of
    appending a number, uses a timestamp to periodically select
    new file names to log to.

    Since this was developed, a TimedRotatingFileHandler was added to
    the Python stdlib. This class is still useful because it allows the period
    to be specified using simple english words.
    """

    def __init__(self, base_filename, mode='a', period='day'):
        self.base_filename = base_filename
        self.mode = mode
        self._set_period(period)
        logging.StreamHandler.__init__(self, None)

    def _set_period(self, period):
        """
        Set the period for the timestamp.  If period is 0 or None, no period
        will be used.
        """
        self._period = period
        if period:
            self._period_seconds = tempora.get_period_seconds(self._period)
            self._date_format = tempora.get_date_format_string(self._period_seconds)
        else:
            self._period_seconds = 0
            self._date_format = ''

    def _get_period(self):
        return self._period

    period = property(_get_period, _set_period)

    def _use_file(self, filename):
        self._ensure_directory_exists(filename)
        self.stream = open(filename, self.mode)

    def _ensure_directory_exists(self, filename):
        dirname = os.path.dirname(filename)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)

    def get_filename(self, t):
        """
        Return the appropriate filename for the given time
        based on the defined period.
        """
        root, ext = os.path.splitext(self.base_filename)
        # remove seconds not significant to the period
        if self._period_seconds:
            t -= t % self._period_seconds
        # convert it to a datetime object for formatting
        dt = datetime.datetime.utcfromtimestamp(t)
        # append the datestring to the filename
        # workaround for datetime.strftime not handling '' properly
        appended_date = (
            dt.strftime(self._date_format) if self._date_format != '' else ''
        )
        if appended_date:
            # in the future, it would be nice for this format
            #  to be supplied as a parameter.
            result = root + ' ' + appended_date + ext
        else:
            result = self.base_filename
        return result

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, ensuring that the currently-
        opened file has the correct date.
        """
        now = time.time()
        current_name = self.get_filename(now)
        try:
            if not self.stream.name == current_name:
                self._use_file(current_name)
        except AttributeError:
            # a stream has not been created, so create one.
            self._use_file(current_name)
        logging.StreamHandler.emit(self, record)

    def close(self):
        """
        Closes the stream.
        """
        try:
            self.stream.close()
        except AttributeError:
            pass


class LogFileWrapper:
    """
    Emulates a file to replace stdout or stderr or
    anothe file object and redirects its output to
    a logger.

    Since data will often be send in partial lines or
    multiple lines, data is queued up until a new line
    is received.  Each line of text is send to the
    logger separately.
    """

    def __init__(self, name, lvl=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.lvl = lvl
        self.queued = ''

    def write(self, data):
        data = self.queued + data
        data = string.split(data, '\n')
        for line in data[:-1]:
            self.logger.log(self.lvl, line)
        self.queued = data[-1]
