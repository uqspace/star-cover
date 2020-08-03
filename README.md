# Star Cover Pages

The python scripts are used to generate star (ch)art diagrams for use as report
cover pages. By default these are centred on
[The University of Queensland](https://www.uq.edu.au/), St Lucia
(at 27.5°S, 153.0°E) with a field of view (FOV) of 180°.

## Configuration

Within the [`config.yaml`](config.yaml) file, the specific date and time of the
observed sky can be changed, along with the location.
The date and time must be specified using any valid format:
```yaml
canonical: 2001-12-15T02:59:43.1Z
iso8601: 2001-12-14t21:59:43.10-05:00
spaced: 2001-12-14 21:59:43.10 -5
```
If the time is not given with an associated timezone, then this will be
automatically determined from the provided coordinates. Please note that, at
coordinates near borders, this might not be correct in rare cases.

The location information is given using latitude and longitude coordinates,
in a single string. Coordinates are given in degrees, along with their
respective cardinality (i.e.)
```yaml
coordinates: '27.0 S, 153.0 E'  # Location of St. Lucia
```
