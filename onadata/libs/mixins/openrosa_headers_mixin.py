# coding: utf-8
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings

# 10,000,000 bytes
DEFAULT_CONTENT_LENGTH = getattr(settings, 'DEFAULT_CONTENT_LENGTH', 10000000)


class OpenRosaHeadersMixin:
    def get_openrosa_headers(self, request, location=True):
        dt = datetime.now(tz=ZoneInfo('UTC')).strftime('%a, %d %b %Y %H:%M:%S %Z')

        data = {
            'Date': dt,
            'X-OpenRosa-Version': '1.0',
            'X-OpenRosa-Accept-Content-Length': DEFAULT_CONTENT_LENGTH
        }

        if location:
            data['Location'] = request.build_absolute_uri(request.path)

        return data
