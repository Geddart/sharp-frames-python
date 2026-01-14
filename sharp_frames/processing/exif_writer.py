"""EXIF metadata writing for JPEG images.

This module handles embedding GPS coordinates into JPEG EXIF metadata
using the piexif library.
"""

import os
from typing import Tuple

import piexif

from .gps_extractor import GPSData


__all__ = ['embed_gps_in_jpeg', 'decimal_to_dms']


def decimal_to_dms(decimal_degrees: float) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    """
    Convert decimal degrees to degrees/minutes/seconds as EXIF rational tuples.

    EXIF stores coordinates as rationals: ((degrees, 1), (minutes, 1), (seconds*100, 100))

    Args:
        decimal_degrees: Coordinate in decimal degrees (absolute value)

    Returns:
        Tuple of three rational tuples: ((deg, 1), (min, 1), (sec*100, 100))
    """
    decimal_degrees = abs(decimal_degrees)
    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60

    # Store seconds with 2 decimal places precision
    seconds_rational = (int(seconds * 100), 100)

    return ((degrees, 1), (minutes, 1), seconds_rational)


def embed_gps_in_jpeg(jpeg_path: str, gps: GPSData) -> bool:
    """
    Embed GPS coordinates into JPEG EXIF metadata.

    Args:
        jpeg_path: Path to the JPEG file to modify
        gps: GPSData containing coordinates to embed

    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(jpeg_path):
        return False

    try:
        # Try to load existing EXIF data
        try:
            exif_dict = piexif.load(jpeg_path)
        except piexif.InvalidImageDataError:
            # No EXIF data, create empty structure
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Build GPS IFD
        gps_ifd = {}

        # Latitude
        lat_ref = "N" if gps.latitude >= 0 else "S"
        gps_ifd[piexif.GPSIFD.GPSLatitudeRef] = lat_ref.encode('ascii')
        gps_ifd[piexif.GPSIFD.GPSLatitude] = decimal_to_dms(gps.latitude)

        # Longitude
        lon_ref = "E" if gps.longitude >= 0 else "W"
        gps_ifd[piexif.GPSIFD.GPSLongitudeRef] = lon_ref.encode('ascii')
        gps_ifd[piexif.GPSIFD.GPSLongitude] = decimal_to_dms(gps.longitude)

        # Altitude
        alt_ref = 0 if gps.altitude >= 0 else 1  # 0 = above sea level, 1 = below
        gps_ifd[piexif.GPSIFD.GPSAltitudeRef] = alt_ref
        # Store altitude in centimeters for precision
        alt_rational = (int(abs(gps.altitude) * 100), 100)
        gps_ifd[piexif.GPSIFD.GPSAltitude] = alt_rational

        # Horizontal positioning error (accuracy) if available
        if gps.accuracy is not None:
            # Store accuracy in centimeters
            accuracy_rational = (int(gps.accuracy * 100), 100)
            gps_ifd[piexif.GPSIFD.GPSHPositioningError] = accuracy_rational

        # Update EXIF dict
        exif_dict["GPS"] = gps_ifd

        # Generate and insert EXIF bytes
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, jpeg_path)

        return True

    except Exception:
        return False
