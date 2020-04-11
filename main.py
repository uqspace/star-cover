import csv

import numpy as np
from svgwrite import Drawing

from reference import ReferenceFrame


if __name__ == '__main__':

    with open('stardata.csv', 'r') as file:
        rawData  = csv.reader(file, delimiter=',')
        starData = np.asarray(list(rawData)).astype(float)

        # Last column represents star magnitude
        coords, magnitude = np.hsplit(starData, [2])

    ref = ReferenceFrame(
        timestamp='2020-04-10 12:00',
        coordinate=(-27.5, 153.0)
    )

    ref.test(coords)
