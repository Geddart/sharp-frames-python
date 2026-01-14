"""GPS metadata extraction from video files.

This module handles extraction of GPS coordinates from video metadata,
particularly Apple QuickTime format used by iPhones.
"""

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Optional


__all__ = ['GPSData', 'extract_gps_from_video', 'parse_iso6709']


@dataclass
class GPSData:
    """GPS coordinate data extracted from video metadata."""
    latitude: float       # Positive = North, Negative = South
    longitude: float      # Positive = East, Negative = West
    altitude: float       # Meters above sea level
    accuracy: Optional[float] = None  # Horizontal accuracy in meters


def parse_iso6709(location_string: str) -> Optional[GPSData]:
    """
    Parse ISO 6709 location string format.

    Format examples:
    - +50.8019+012.9069+311.398/  (lat+lon+alt)
    - +50.8019+012.9069/          (lat+lon only)
    - +50.8019-012.9069+311.398/  (west longitude)

    Args:
        location_string: ISO 6709 formatted location string

    Returns:
        GPSData if parsing successful, None otherwise
    """
    if not location_string:
        return None

    # ISO 6709 pattern: ±DD.DDDD±DDD.DDDD±AAA.AAA/
    # Latitude: ±DD.DDDD (2 digits before decimal)
    # Longitude: ±DDD.DDDD (3 digits before decimal)
    # Altitude: ±AAA.AAA (optional)
    pattern = r'^([+-]\d+\.\d+)([+-]\d+\.\d+)([+-]\d+\.?\d*)?/?$'
    match = re.match(pattern, location_string.strip())

    if not match:
        return None

    try:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
        altitude = float(match.group(3)) if match.group(3) else 0.0

        return GPSData(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude
        )
    except (ValueError, TypeError):
        return None


def extract_gps_from_video(video_path: str) -> Optional[GPSData]:
    """
    Extract GPS coordinates from video metadata using ffprobe.

    Supports Apple QuickTime format (com.apple.quicktime.location.ISO6709).

    Args:
        video_path: Path to the video file

    Returns:
        GPSData if GPS metadata found, None otherwise
    """
    ffprobe_executable = 'ffprobe.exe' if os.name == 'nt' else 'ffprobe'

    cmd = [
        ffprobe_executable, '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        os.path.normpath(video_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        tags = data.get('format', {}).get('tags', {})

        # Try Apple QuickTime location format
        location_str = tags.get('com.apple.quicktime.location.ISO6709')
        if location_str:
            gps = parse_iso6709(location_str)
            if gps:
                # Try to get accuracy
                accuracy_str = tags.get('com.apple.quicktime.location.accuracy.horizontal')
                if accuracy_str:
                    try:
                        gps.accuracy = float(accuracy_str)
                    except ValueError:
                        pass
                return gps

        # Could add support for other metadata formats here (e.g., Android)

        return None

    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, OSError):
        return None
