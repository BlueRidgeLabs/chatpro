from __future__ import unicode_literals

import datetime
import pytz

ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def format_iso8601(_datetime):
    return _datetime.astimezone(pytz.UTC).strftime(ISO8601_FORMAT)


def parse_iso8601(text):
    return datetime.datetime.strptime(text, ISO8601_FORMAT)


def intersection(a, b):
    """ return the intersection of two lists """
    return list(set(a) & set(b))