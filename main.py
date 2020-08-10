import warnings

import numpy as np

from skyfield.api import Star, load
from skyfield.data import hipparcos, stellarium
from skyfield.toposlib import Topos

import svgwrite as svg
import yaml

from util import stereographicProjection

UQS_BLUE = '#091544'
SCALE    = 1000


# Load timescale and ephemeris from JPL
timescale = load.timescale()
ephemeris = load('de421.bsp')


with open('config.yaml') as file:
    config = yaml.full_load(file)


# Create observer location in SkyField coordinate object
location = ephemeris['earth'] + Topos(*config['coordinates'].split(','))

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
    # Update the datetime
    config['datetime'].replace(tzinfo=timezone(timezoneString))

timestamp = timescale.from_datetime(config['datetime'])

# The Hipparcos mission provides our star catalog.

with load.open(hipparcos.URL) as file:
    stars = hipparcos.load_dataframe(file)

# Now that we have constructed our projection, compute the x and y
# coordinates that each star and the comet will have on the plot.

star_positions = location.at(timestamp).observe(Star.from_dataframe(stars))
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    alt, az, _ = star_positions.apparent().altaz()

star_centers = SCALE * np.stack(stereographicProjection(
    alt.radians, az.radians + np.pi)).T


def brightness(magnitude):
    return 20 * 100**(-0.02*magnitude)


star_markers  = brightness(stars['magnitude'].values)
star_markers -= brightness(config['output']['max_magnitude'])  # Normalise
bright, = np.where(np.logical_and(
    star_markers > 1,
    np.any(abs(star_centers) <= 1000, axis=1),
))

# The constellation outlines come from Stellarium. We make a list of the stars
# at which each edge stars, and the star at which each edge ends.

url = ('https://raw.githubusercontent.com/Stellarium/stellarium/'
       'master/skycultures/western_SnT/constellationship.fab')

with load.open(url) as file:
    constellations = stellarium.parse_constellations(file)

# The constellation references stars by their ID, which is stored as the index
# in the hipparcos dataframe.

edges = [
    ( stars.index.get_loc(start), stars.index.get_loc(end) )
    for _, edges in constellations
    for (start, end) in edges
]

# Time to build the map!

dwg = svg.Drawing(filename='starcover.svg', size=('300mm', '300mm'))
dwg.viewbox(minx=-1000, miny=-1000, width=2000, height=2000)

star_group = dwg.g(
    fill=UQS_BLUE,
    fill_opacity=1,
    stroke='none'
)

for center, marker in zip(star_centers[bright], star_markers[bright]):
    star_group.add(dwg.circle(
        center=center.round(2),
        r=marker.round(1),
    ))

constellation_group = dwg.g(
    stroke=UQS_BLUE,
    stroke_width=0.25,
    stroke_opacity=0.25,
    fill='none'
)

for (start, end) in edges:
    constellation_group.add(dwg.line(
        start=star_centers[start].round(2),
        end=star_centers[end].round(2)
    ))

dwg.add(star_group)
dwg.add(constellation_group)
dwg.save(pretty=True, indent=4)
