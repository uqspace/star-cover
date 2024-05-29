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


def cylindricalProjection(alt, az, shifted=False):
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
    if shifted:
        az += np.pi
        alt *= -1
    x = np.interp(az, [0, 2*np.pi], [-1, +1], period=2*np.pi)
    y = np.sin(alt)

    return x, y


def shiftedCylindricalProjection(alt, az):
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
    az += np.pi
    alt *= -1
    x = np.interp(az, [0, 2*np.pi], [-1, +1], period=2*np.pi)
    y = np.sin(alt)

    return x, y
