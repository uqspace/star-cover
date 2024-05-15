from dataclasses import dataclass

from skyfield.api import load, wgs84
from skyfield import positionlib

from .schema import Observer

@dataclass
class GeographicCoordinate:
    lat: float
    lon: float

    def findTimezone(self) -> str:

        from timezonefinder import TimezoneFinder

        searchEngine   = TimezoneFinder(in_memory=True)
        timezoneString = searchEngine.timezone_at(lat=self.lat, lng=self.lon)

        if timezoneString is None:
            raise ValueError(f"No valid timezone at {self}")

        return timezoneString


def fromConfig(config: Observer) -> positionlib.Barycentric:
    # Load data from skyfield
    planets = load("de421.bsp")
    timescale = load.timescale()

    # Validate config data
    coordinate = GeographicCoordinate(**config.location)
    timestamp = config.datetime
    if timestamp.tzinfo is None:
        from zoneinfo import ZoneInfo
        timestamp = timestamp.replace(tzinfo=ZoneInfo(coordinate.findTimezone()))

    # Construct location in skyfield data-format
    time = timescale.from_datetime(timestamp)
    place = planets['earth'] + wgs84.latlon(
        latitude_degrees=coordinate.lat,
        longitude_degrees=coordinate.lon
    )

    return place.at(time)
