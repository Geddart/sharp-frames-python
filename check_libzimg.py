#!/usr/bin/env python3
"""Check if FFmpeg has libzimg/zscale support for HDR to SDR tone mapping."""

import subprocess
import sys
import os


def check_ffmpeg_zscale():
    """Check FFmpeg for zscale filter availability."""
    ffmpeg_executable = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'

    print(f"Platform: {sys.platform} (os.name: {os.name})")
    print(f"Looking for: {ffmpeg_executable}")
    print("-" * 50)

    # Check if FFmpeg is available
    try:
        result = subprocess.run(
            [ffmpeg_executable, '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"FFmpeg found: {version_line}")
        else:
            print(f"ERROR: FFmpeg returned error code {result.returncode}")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print(f"ERROR: {ffmpeg_executable} not found in PATH")
        print("\nTo fix this on Windows:")
        print("  1. Download FFmpeg from https://www.gyan.dev/ffmpeg/builds/")
        print("     (Choose 'ffmpeg-release-full' for libzimg support)")
        print("  2. Extract and add the bin folder to your PATH")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

    print("-" * 50)

    # Check for zscale filter
    try:
        result = subprocess.run(
            [ffmpeg_executable, '-filters'],
            capture_output=True,
            text=True,
            timeout=10
        )

        has_zscale = 'zscale' in result.stdout
        has_tonemap = 'tonemap' in result.stdout
        has_colorspace = 'colorspace' in result.stdout

        print("\nHDR/Color Processing Filters:")
        print(f"  zscale (libzimg):  {'YES' if has_zscale else 'NO'}")
        print(f"  tonemap:           {'YES' if has_tonemap else 'NO'}")
        print(f"  colorspace:        {'YES' if has_colorspace else 'NO'}")

        print("-" * 50)

        if has_zscale:
            print("\n[OK] libzimg IS available!")
            print("     HDR to SDR tone mapping will use high-quality zscale pipeline.")
            return True
        else:
            print("\n[WARNING] libzimg is NOT available!")
            print("          HDR to SDR conversion will use fallback (may clip highlights).")
            print("\nTo get libzimg support on Windows:")
            print("  1. Download FFmpeg 'full' build from https://www.gyan.dev/ffmpeg/builds/")
            print("     The 'full' builds include libzimg")
            print("  2. Or use: winget install Gyan.FFmpeg.Full")
            print("  3. Or use: choco install ffmpeg-full")
            return False

    except Exception as e:
        print(f"ERROR checking filters: {e}")
        return False


def check_build_configuration():
    """Check FFmpeg build configuration for zimg."""
    ffmpeg_executable = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'

    try:
        result = subprocess.run(
            [ffmpeg_executable, '-buildconf'],
            capture_output=True,
            text=True,
            timeout=10
        )

        has_zimg = '--enable-libzimg' in result.stdout

        print("\nBuild Configuration:")
        print(f"  --enable-libzimg:  {'YES' if has_zimg else 'NO'}")

        if not has_zimg and '--enable-' in result.stdout:
            # Show some relevant enabled features
            lines = result.stdout.split()
            relevant = [l for l in lines if any(x in l.lower() for x in ['color', 'scale', 'zimg', 'hdr'])]
            if relevant:
                print("\n  Relevant build options found:")
                for opt in relevant[:10]:
                    print(f"    {opt}")

    except Exception as e:
        print(f"Could not check build config: {e}")


if __name__ == '__main__':
    print("=" * 50)
    print("Sharp Frames - libzimg/zscale Support Check")
    print("=" * 50)
    print()

    result = check_ffmpeg_zscale()
    check_build_configuration()

    print()
    print("=" * 50)
    sys.exit(0 if result else 1)
