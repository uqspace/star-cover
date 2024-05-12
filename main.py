from dataclasses import dataclass

import numpy as np
import pandas as pd

from skyfield.api import Star, load, wgs84
from skyfield.data import hipparcos, stellarium

import svgwrite as svg
from svgwrite.shapes import Circle, Line, Rect
import tomlkit as toml

from util import stereographicProjection, cylindricalProjection


@dataclass
class Coordinate:
    lat: float
    lon: float


# UQ_PURPLE = '#51247A'
UQ_PURPLE = '#000000'
SCALE     = 1000


# Load timescale and ephemeris from JPL
timescale = load.timescale()
ephemeris = load('de421.bsp')


with open('config.toml') as file:
    config = toml.load(file).unwrap()


# Create observer location in SkyField coordinate object
coord = Coordinate(**config['coordinates'])
topos = wgs84.latlon(longitude_degrees=coord.lon, latitude_degrees=coord.lat)
location = ephemeris['earth'] + topos

# Ensure the given datetime is assigned a timezone
if not config['datetime'].tzinfo:
    # Load packages to find timezone from coordinates
    from pytz import timezone
    from timezonefinder import TimezoneFinderL

    searchEngine   = TimezoneFinderL(in_memory=True)
    timezoneString = searchEngine.timezone_at(
        lng=location.longitude,
        lat=location.latitude
    )
    if timezoneString is None:
        raise ValueError(f"No valid timezone at ({location.longitude}, {location.latitude})")
    # Update the datetime
    config['datetime'].replace(tzinfo=timezone(timezoneString))

timestamp = timescale.from_datetime(config['datetime'])

# The Hipparcos mission provides our star catalog.


with load.open(hipparcos.URL) as file:
    stars = hipparcos.load_dataframe(file)
    # Do some data cleaning. Sort and fill, so the hip ID corresponds to row index
    stars = stars.reindex(index=pd.RangeIndex(0, stars.index.max()+1), fill_value=np.nan)


# Now that we have constructed our projection, compute the x and y
# coordinates that each star and the comet will have on the plot.

alt, az, _ = location.at(timestamp) \
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
