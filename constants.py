"""
This file contains constant values used by the program.
"""

# List of commonly used baud rates, add more if required.
import numpy as np

COMMON_BAUD_RATES = [
    2400,
    4800,
    9600,
    19200,
    38400,
    57600,
    115200,
    230400,
    460800,
    576000
]

# Points used for visual representation of the ultrasound probe in a 3D space. Order matters.
PROBE_POINTS = [
    [0, 0, 0],
    [-1, -.3, 0],
    [-2, -.8, 0],
    [0, -6, 0],
    [2, -.8, 0],
    [1, -.3, 0]]

# Default azimuth value used for the 3D plot.
AZIMUTH = 30

# Available return rates for the IMU. The Witmotion library limits the number of return rates that are available.
IMU_RATE_OPTIONS = [
    "0.2Hz",
    "0.5Hz",
    "1Hz",
    "2Hz",
    "5Hz",
    "10Hz",
    "20Hz",
    "50Hz",
    "100Hz",
    "200Hz"
]

# Number of available video sources. It is highly unlikely that more than 5 sources will be present, but if there are
# more this value can be increased. The values will range from 0 (inclusive) to VIDEO_SOURCES (inclusive)
SIGNAL_SOURCES = 5

# The width and height of the displayed image. The input signal will be resized to fit these dimensions.
DISPLAY_DIMENSIONS = (1024, 576)

# Default frame rate of the video signal. This is dependent on the video signal source and the hardware being used.
DEFAULT_FRAME_RATE = 100

# Default signal dimensions. HD is chosen, if it is not available the nearest lower resolution will be used.
DEFAULT_SIGNAL_DIMENSIONS = [1920, 1080]

# Common video signal dimensions, width x height
COMMON_SIGNAL_DIMENSIONS = [
    ['640x480'],
    ['800x600'],
    ['1280x720'],
    ['1920x1080']]

# Default scan depth saved to data.txt file.
DEFAULT_SCAN_DEPTH = 150

# If a point is added within this radius, the nearest point is removed instead (as a fraction).
DEFAULT_POINT_RADIUS = 0.01

# Constant used in the bullet equation.
BULLET_CONSTANT = 5 * np.pi / 24
# BULLET_CONSTANT = 0.65
