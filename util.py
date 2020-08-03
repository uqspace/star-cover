import numpy as np


def stereographicProjection(alt, az):
    """Project stars onto a 2D plane stereographically.

    Parameters
    ----------
    alt : np.ndarray
        The altitude of a star, relative to an observer.
        Values are processed as radians.
    az : np.ndarray
        The azimuth of a star, relative to an observer.
        Values are processed as radians.

    Returns
    -------
    (np.ndarray, np.ndarray)
        The (x, y) coordinates of each star, projected onto a 2D plane
        stereographically.
    """
    x = np.cos(alt) * np.sin(az)
    y = np.cos(alt) * np.cos(az)
    z = np.sin(alt)

    return x/(1+z), y/(1+z)


def cylindricalProjection(alt, az):
    """Project stars onto an equirectangular plan.

    Parameters
    ----------
    alt : np.ndarray
        The altitude of a star, relative to an observer.
        Values are processed as radians.
    az : np.ndarray
        The azimuth of a star, relative to an observer.
        Values are processed as radians.

    Returns
    -------
    (np.ndarray, np.ndarray)
        The (x, y) coordinates of each star, calculated using an
        equirectangular projection, to maintain equal areas.
    """
    x = np.interp(az, [0, 2*np.pi], [-1, +1])
    y = np.sin(alt)

    return x, y
