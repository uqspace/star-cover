from dataclasses import dataclass
from pathlib import PurePath

import numpy as np
import pandas as pd

from skyfield.api import Star, load
from skyfield.data import hipparcos, stellarium

import svgwrite as svg
from svgwrite.shapes import Circle, Line, Rect
import tomlkit as toml
import papersize

from starcover import observer
from starcover.schema import Config

from util import stereographicProjection, cylindricalProjection


RESOLUTION = 1000


@dataclass
class Page:
    width: float
    height: float
    unit: str = "mm"

    @classmethod
    def setUnit(cls, unit: str):
        if unit not in papersize.UNITS:
            raise ValueError(f"Unknown unit `{unit}`")
        cls.unit = unit

    @classmethod
    def fromString(cls, string: str) -> 'Page':
        width, height = papersize.parse_papersize(string, unit = cls.unit)
        return Page(width=float(width), height=float(height))

    @property
    def size(self) -> tuple[str, str]:
        return (str(self.width) + self.unit, str(self.height) + self.unit)


@dataclass
class Display:
    width: int
    height: int

    @staticmethod
    def fromPage(page: Page, resolution: float) -> 'Display':
        # Ensure that the width and height are odd (2k + 1 for integer k)
        width = int(page.width * resolution / 2) * 2 + 1
        height = int(page.height * resolution / 2) * 2 + 1
        return Display(width=width, height=height)

    @property
    def size(self):
        return (self.width, self.height)

    @property
    def bottomLeft(self):
        return (-self.width/2, -self.height/2)


with open('config.toml') as file:
    config = Config(**toml.load(file).unwrap())

page = Page.fromString(config.output.size)
display = Display.fromPage(page, resolution=5)

# The Hipparcos mission provides our star catalog.

with load.open(hipparcos.URL) as file:
    stars = hipparcos.load_dataframe(file)
    # Do some data cleaning. Sort and fill, so the hip ID corresponds to row index
    stars = stars.reindex(index=pd.RangeIndex(0, stars.index.max()+1), fill_value=np.nan)

alt, az, _ = observer.fromConfig(config.observer) \
    .observe(Star.from_dataframe(stars)) \
    .apparent() \
    .altaz()

projection = cylindricalProjection
# projection = stereographicProjection
star_centers = np.stack(projection(alt.radians, az.radians), axis=1)
star_centers = np.round(star_centers * display.size / 2, decimals=2)


def brightness(magnitude):
    return 20 * 100**(-0.02*magnitude)


star_markers  = brightness(stars['magnitude'].values)
star_markers -= brightness(config.output.max_magnitude)  # Normalise
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

dwg = svg.Drawing(
    filename=str(PurePath(config.output.name).with_suffix(".svg")),
    size=page.size
)
dwg.viewbox(
    minx=-display.width//2, miny=-display.height//2, 
    width=display.width, height=display.height
)

clip_path = dwg.defs.add(dwg.clipPath(id="clipCanvas"))
clip_path.add(Rect(insert=display.bottomLeft, size=display.size))

star_group = dwg.g(
    clip_path=clip_path.get_funciri(),
    **config.style.stars.flat_dump()
)

constellation_group = dwg.g(
    clip_path=clip_path.get_funciri(),
    **config.style.constellations.flat_dump()
)

for center, marker in zip(star_centers[bright], star_markers[bright]):
    # Move checking for the center to a filter here
    star_group.add(Circle(center=center, r=marker))

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
        if az.radians[startID] - az.radians[endID] > np.pi:
            # Create two new fake stars, and duplicate the lines
            fakeStart = start - [display.width, 0]
            fakeEnd = end + [display.width, 0]

            constellation_group.add(Line(start=fakeStart, end=end))
            constellation_group.add(Line(start=start, end=fakeEnd))

        elif az.radians[endID] - az.radians[startID] > np.pi:
            # Create two new fake stars, and duplicate the lines
            fakeStart = start + [display.width, 0]
            fakeEnd = end - [display.width, 0]

            constellation_group.add(Line(start=fakeStart, end=end))
            constellation_group.add(Line(start=start, end=fakeEnd))

        else:
            constellation_group.add(Line(start=start, end=end))

dwg.add(star_group)
dwg.add(constellation_group)
dwg.save(pretty=True, indent=4)
