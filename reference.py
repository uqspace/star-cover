from datetime import datetime

import numpy as np
from numpy import sin, cos, arcsin, arccos, tan
from timezonefinder import TimezoneFinder
from pytz import timezone, UTC

from util import vectorize

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY  = 3600 * 24
EPOCH = datetime(year=2000, month=1, day=1, tzinfo=UTC)


class ReferenceFrame:

    def __init__(self, timestamp=None, coordinate=(0, -90)):
        self.latitude, self.longitude = coordinate
        self.timezone = self._findTimezone(coordinate)

        # Create and adjust datetime to local timezone
        self.datetime = (
            datetime.fromisoformat(timestamp)
            if timestamp else datetime.today()
        )
        self.datetime = self.datetime.replace(tzinfo=self.timezone)

        secondsFromEpoch = UTC.normalize(self.datetime) - EPOCH
        daysFromEpoch    = secondsFromEpoch.total_seconds() / SECONDS_PER_DAY

        secondsFromUT = self.timezone.utcoffset(self.datetime)
        hoursFromUT   = secondsFromUT.total_seconds() / SECONDS_PER_HOUR

        # Local Siderial Time
        self.lst = (
            + 0.985647 * daysFromEpoch
            + 15 * (hoursFromUT % 24)
            + self.longitude
            + 100.46
        ) % 360

    def _findTimezone(self, coordinate):
        lat, lng = coordinate

        searchEngine = TimezoneFinder()
        timezoneString = searchEngine.timezone_at(lat=lat, lng=lng)

        return timezone(timezoneString)

    def toLocal(self, coords):

        @vectorize(signature='(),(),(n)->()')
        def _transform(lat, lst, coord):
            ra, dec = coord
            ha = (lst - ra) % 360  # Hour Angle

            sin_alt = sin(dec)*sin(lat) + cos(dec)*cos(lat)*cos(ha)
            alt     = np.arcsin(sin_alt)

            cos_az  = sin(dec)/(cos(alt)*cos(lat)) - tan(alt)*tan(lat)
            az      = np.arccos(cos_az)

            return alt, az

        return _transform(self.latitude, self.lst, coords)
