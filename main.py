from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from skyfield.api import Star, load, wgs84
from skyfield.data import hipparcos, stellarium

from skyfield import positionlib

import svgwrite as svg
from svgwrite.shapes import Circle, Line, Rect
import tomlkit as toml

from util import stereographicProjection, cylindricalProjection


# UQ_PURPLE = '#51247A'
UQ_PURPLE  = '#000000'
SCALE      = 1000
RESOLUTION = 1000


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


def fromConfig(config) -> positionlib.Barycentric:
    # Load data from skyfield
    planets = load("de421.bsp")
    timescale = load.timescale()

    # Validate config data
    coordinate = GeographicCoordinate(**config["location"])
    timestamp: datetime = config['datetime']
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


with open('config.toml') as file:
    config = toml.load(file).unwrap()


# # The Hipparcos mission provides our star catalog.

with load.open(hipparcos.URL) as file:
    stars = hipparcos.load_dataframe(file)
    # Do some data cleaning. Sort and fill, so the hip ID corresponds to row index
    stars = stars.reindex(index=pd.RangeIndex(0, stars.index.max()+1), fill_value=np.nan)


observer = fromConfig(config['observer'])

alt, az, _ = observer \
    .observe(Star.from_dataframe(stars)) \
    .apparent() \
    .altaz()

projection = cylindricalProjection
# projection = stereographicProjection
star_centers = np.stack(projection(alt.radians, az.radians), axis=1)
star_centers = np.round(SCALE * star_centers, decimals=2)


def brightness(magnitude):
    return 20 * 100**(-0.02*magnitude)


star_markers  = brightness(stars['magnitude'].values)
star_markers -= brightness(config['output']['max_magnitude'])  # Normalise
star_markers  = np.round(star_markers, decimals=1)
bright, = np.where(np.logical_and(
    # Ensure stars are bright enough
    star_markers > 1,
    # Ensure stars are within view-field
    np.all(abs(star_centers) <= 1000, axis=1),
))

# The constellation outlines come from Stellarium. We make a list of the stars
# at which each edge stars, and the star at which each edge ends.

url = ("https://raw.githubusercontent.com/Stellarium/stellarium/"
       "master/skycultures/modern_st/constellationship.fab")

with load.open(url) as file:
    constellations = stellarium.parse_constellations(file)

# Time to build the map!

dwg = svg.Drawing(filename='starcover.svg', size=('300mm', '300mm'))
dwg.viewbox(minx=-1000, miny=-1000, width=2000, height=2000)
clip_path = dwg.defs.add(dwg.clipPath(id="clipCanvas"))
clip_path.add(Rect(insert=(-1000, -1000), size=(2000, 2000)))

star_group = dwg.g(
    fill=UQ_PURPLE,
    fill_opacity=1,
    stroke=UQ_PURPLE,
    stroke_width=0.25,
    clip_path='url(#clipCanvas)'
)

for center, marker in zip(star_centers[bright], star_markers[bright]):
    star_group.add(Circle(center=center, r=marker))

constellation_group = dwg.g(
    stroke=UQ_PURPLE,
    stroke_width=0.5,
    stroke_opacity=0.5,
    fill='none',
    clip_path='url(#clipCanvas)'
)

for name, edges in constellations:
    for (startID, endID) in edges:
        start, end = star_centers[[startID, endID]]

        if any(np.isnan(start)):
            print(f"Skipping ill-defined star {startID} in constellation {name}")
            continue
        elif any(np.isnan(end)):
            print(f"Skipping ill-defined star {endID} in constellation {name}")
            continue

        # Check if we've crossed the "split" on the sky at az = 2pi
        if start[0] - end[0] > SCALE:
            # Create two new fake stars, and duplicate the lines
            fakeStart = start - [2*SCALE, 0]
            fakeEnd = end + [2*SCALE, 0]

            constellation_group.add(Line(start=fakeStart, end=end))
            constellation_group.add(Line(start=start, end=fakeEnd))

        elif end[0] - start[0] > SCALE:
            # Create two new fake stars, and duplicate the lines
            fakeStart = start + [2*SCALE, 0]
            fakeEnd = end - [2*SCALE, 0]

            constellation_group.add(Line(start=fakeStart, end=end))
            constellation_group.add(Line(start=start, end=fakeEnd))

        else:
            constellation_group.add(Line(start=start, end=end))

dwg.add(star_group)
dwg.add(constellation_group)
dwg.save(pretty=True, indent=4)
