from __future__ import unicode_literals

import datetime


def parse_iso8601(text):
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ")
