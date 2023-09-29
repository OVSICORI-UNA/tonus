#!/usr/bin/env python


"""
"""


# Python Standard Library

# Other dependencies
import numpy as np
import pandas as pd

from numba import jit
from scipy.fft import rfft
from scipy.signal.windows import tukey
from tonus.detection.obspy2numpy import st2windowed_data

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'lvmzxc@gmail.com'


@jit(nopython=True)
def _get_cft(Sxx, k, _bin_width):
    """
    Compute the characteristic function (Tonality) for spectral data.

    Parameters:
    ----------
    Sxx : numpy.ndarray
        Input spectral data as an Nx2 numpy.ndarray.
    k : int
        Number of frequency peaks to identify.
    _bin_width : float
        Width of frequency bins for peak detection (in samples).

    Returns:
    -------
    cft : numpy.ndarray
        Computed characteristic function (tonality) values
    """
    # Initialize an array to store the computed tonality values.
    cft = np.zeros(len(Sxx), dtype=np.float64)

    # Iterate through each frame
    for j, Sx in enumerate(Sxx):

        # Sort the spectrum in descending order and get the sorted indices.
        index = np.argsort(-Sx)

        # Initialize variables for cumulative tonality and effective peaks.
        c, effective = 0, []

        # Iterate through the sorted spectrum.
        for i, idx in enumerate(index):
            nxt = False

            # Check if the current bin is near previous coherent peaks.
            if i > 0:
                for e in effective:
                    if (idx < e+_bin_width/2) and (idx > e-_bin_width/2):
                        nxt = True
                        break
            # If the bin is near a previous peak, skip it.
            if nxt:
                continue

            # If we've identified 'k' coherent peaks, stop the search.
            if len(effective) >= k:
                break

            # Determine the left and right boundaries of the frequency bin.
            left = int(idx - _bin_width/2)
            right = int(idx + _bin_width/2)

            # Initialize variables for padding.
            left_pad, right_pad = 0, 0

            # Handle cases where the bin extends beyond the spectrum.
            if left < 0:
                left_pad = -1*left
                left = 0

            if right >= len(Sx):
                right_pad = right - len(Sx) + 1
                right = len(Sx) - 1

            # Slice
            Sx_slice = np.zeros(_bin_width, dtype=np.float64)
            Sx_slice[left_pad:left_pad+right-left] = Sx[left:right]

            # If padding is applied, fill it with the median value.
            if left_pad != 0:
                Sx_slice[:left_pad] = np.median(Sx[left:right])
            if right_pad != 0:
                Sx_slice[-right_pad:] = np.median(Sx[left:right])

            # Normalize
            Sx_slice = Sx_slice/Sx_slice.max()

            # Median
            med = np.median(Sx_slice)

            # Tonality
            c += (1/med)

            # Add the index of the coherent peak to the 'effective' list.
            effective.append(idx)
        cft[j] = c
    return cft


def get_cft(tr, short_win, overlap, pad, k, bin_width, long_win):
    """
    Compute the characteristic function (cumulative tonality)
    It replaces the data in the trace object

    Parameters:
    -----------
    tr : obspy.Trace
        The seismic data trace to analyze.
    short_win : float
        Length of the short time window (seconds) for computing CT.
    overlap : float
        Overlap ratio between short windows (0 to 1).
    pad : float
        Tukey window parameter for tapering the data (0 to 1).
    k : int
        Number of coherent frequency peaks to identify.
    bin_width : float
        Width of frequency bins for peak detection (Hz).
    long_win : float
        Length of the long time window (seconds) for smoothing.

    Returns:
    --------
    None

    Note:
    -----
    - This function modifies the input 'tr' object in-place.
    """
    # Slice the data into windows
    utcdatetimes, data_windowed = st2windowed_data(tr, short_win, overlap)

    data_windowed = data_windowed[0]
    data_windowed = data_windowed.astype(float)
    data_windowed *= tukey(data_windowed.shape[1], alpha=pad)  # taper

    # Frequency array
    freq = np.fft.rfftfreq(data_windowed.shape[1], tr.stats.delta)

    # Determine the bin width in samples
    nyquist = tr.stats.sampling_rate/2
    fft_sampling_rate = len(freq)/nyquist  # Samples per Hz
    _bin_width = int(bin_width*fft_sampling_rate)

    # FFT computation
    Sxx = np.abs(rfft(data_windowed))

    # Cumulative tonality computation
    cft = _get_cft(Sxx, k, _bin_width)

    # Smooth the characteristic function
    delta = short_win - overlap*short_win
    _long_win = int(long_win/delta)
    cf = pd.Series(cft)
    cft = cf / cf.rolling(_long_win).mean()
    cft = cft.to_numpy()

    # Replace data of the tr object
    tr.data = cft
    tr.stats.delta = delta
    tr.stats.sampling_rate = 1/delta
    tr.stats.starttime = utcdatetimes[0]
    return


if __name__ == '__main__':
    pass
