"""
Shared preprocessing: conversion to luminance (Y channel of YCbCr) on a
square image. No crop, no filter (Haar cascade approach abandoned: too many
discards / false detections, see project discussion).
"""

import numpy as np
import cv2

SQUARE_SIZE = (160, 160)


def to_luminance(image: np.ndarray) -> np.ndarray:
    """
    Builds a 3-channel tensor (Y, B, R): Y = luminance (from YCbCr), B and R
    = raw blue and red channels from the original RGB image. The input
    image is already square (resize done upstream, e.g. by
    flow_from_directory).

    Why 3 channels (not just Y): the Intel GPU backend (ITEX/oneDNN) does
    not support convolution with a single-channel input (error "output
    depth must be evenly divisible by number of groups") -- a 3-channel
    input is required anyway for the first Conv2D. The network's parameter
    count does NOT depend on channel content (only on the count), so we
    might as well put 3 channels with real information (Y, B, R) instead of
    replicating Y three times.

    Input: (H, W, 3) RGB, values 0..255.
    Output: (H, W, 3) float32, values 0..255 -- channels [Y, B, R].
    """
    ycc = cv2.cvtColor(image.astype("uint8"), cv2.COLOR_RGB2YCrCb)
    y = ycc[:, :, 0]
    b = image[:, :, 2]
    r = image[:, :, 0]
    stacked = np.stack([y, b, r], axis=-1)  # (H, W) x3 -> (H, W, 3)
    return stacked.astype("float32")
