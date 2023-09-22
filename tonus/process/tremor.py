#!/usr/bin/env python


"""
Harmonic tremor analysis module

This module provides functions for harmonic tremor data analysis, focusing on
pitch and harmonics (overtones) determination.
"""


# Python Standard Library

# Other dependencies
import numpy as np

from numba import jit
from scipy.fft import rfft
from scipy.signal import find_peaks, medfilt
from scipy.signal.windows import tukey
from tonus.detection.obspy2numpy import st2windowed_data

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'laat@umich.edu'


@jit(nopython=True)
def yin_block(data, fs, w_size, tau_max, thresh):
    '''
    Estimate pitch for a windowed chunk of signal using the YIN algorithm.

    Parameters:
    -----------
    data : numpy.ndarray
        1D array containing time series data.
    fs : float
        Sampling frequency (Hz).
    w_size : int
        Window size (samples).
    tau_max : int
        Max lag for the difference function.
    thresh : float
        Threshold for identifying the first minimum in D.

    Returns:
    --------
    pitch : float
        Estimated fundamental frequency (Hz). Returns NaN if no reliable pitch
        estimate is found.
    confidence : float
        Confidence level of the pitch estimate. Returns NaN if no reliable
        pitch estimate is found.
    '''
    # Initialize an array to store the ACF (auto-correlation function)
    r = np.zeros(tau_max)

    # Step 1: The autocorrelation method (Eq. 1)
    for i in range(tau_max):
        vec = np.zeros(w_size, dtype=np.float64)

        # Create a vector for the current lag
        vec[:] = data[:w_size] - data[i:w_size+i]

        # Squared dot product and store it in ACF
        r[i] = np.dot(vec, vec)

    # Initialize an array to store the
    d = np.zeros(tau_max)
    # The sum in Eq. 8
    s = r[0]
    d[0] = 1

    # Step 3: cumulative mean normalized difference function
    for i in range(1, tau_max):
        s += r[i]
        d[i] = r[i] / ((1/i)*s)

    # Step 4: Absolute threshold
    idcs = np.where(d < thresh)

    # Check if no reliable pitch estimate is found
    if len(d[idcs]) == 0:
        return np.nan, np.nan

    # Calculate the pitch and its confidence
    return min(d[idcs]), fs/idcs[0][np.argmin(d[idcs])]


def _detect_f1(data, fs, w_size, tau_max, hop_size, freqmin, thresh):
    """
    Detect the fundamental frequency (F1) in a time-varying signal.

    This function estimates the fundamental frequency (F1) of a time-varying
    signal using the YIN algorithm on overlapping windows. The detected F1
    values are computed over time and returned along with associated time
    instants and confidence values.

    Parameters
    ----------
    data : numpy.ndarray
        1D array containing the input data.
    fs : float
        Sampling frequency (Hz).
    w_size : int
        Window size (samples) for YIN analysis.
    tau_max : int
        Maximum lag for the difference function in YIN.
    hop_size : int
        Hop size (samples) between consecutive analysis windows.
    freqmin : float
        Minimum reliable fundamental frequency (Hz). F1 values below this
        threshold will be replaced with NaN.
    thresh : float
        Threshold for identifying the first minimum in YIN's difference
        function.

    Returns
    -------
    tau : numpy.ndarray
        Confidence values corresponding to the detected F1 values.
    t : numpy.ndarray
        Time instants (s) at which F1 values are estimated.
    pitch : numpy.ndarray
        Estimated fundamental frequency (F1) values (Hz).
        Values below 'freqmin' are replaced with NaN.

    """
    # Calculate the number of analysis windows (hops)
    num_hops = (len(data) - w_size - tau_max) // hop_size + 1

    # Initialize arrays to store results
    pitch = np.zeros(num_hops)
    tau = np.zeros(num_hops)

    # Initialize window indices
    idx0 = 0
    idx1 = idx0 + w_size + tau_max

    # Iterate over analysis windows
    for n in range(num_hops):
        # Call the yin_block function to estimate pitch and confidence
        c, p = yin_block(data[idx0:idx1], fs, w_size, tau_max, thresh)

        # Check if estimated pitch is above the minimum threshold
        if p > freqmin:
            pitch[n] = p
            tau[n] = c
        else:
            # Replace with NaN if below threshold
            pitch[n] = np.nan
            tau[n] = np.nan

        # Update window indices for the next analysis window
        idx0 += hop_size
        idx1 += hop_size

    # Calculate time instants for each analysis window
    time_hop = hop_size / fs
    t = np.linspace(0, time_hop * num_hops, num_hops)
    t += time_hop / 2
    return tau, t, pitch


def detect_f1(tr, window_s, overlap, freqmin, thresh):
    """
    Detect the fundamental frequency (F1) in a time series signal.

    This function performs F1 detection by processing a time series signal
    using the YIN algorithm.

    Parameters:
    -----------
    tr : ObsPy Trace object
        The time series data to be analyzed.
    window_s : float
        Duration of the analysis window (seconds).
    overlap : float
        Overlap between consecutive analysis windows (fraction).
    freqmin : float
        Minimum frequency (Hz) for identifying the fundamental frequency.
    thresh : float
        Threshold for identifying the first minimum in the YIN algorithm.

    Returns
    -------
    tau : numpy.ndarray
        Confidence values corresponding to the detected F1 values.
    t : numpy.ndarray
        Time instants (s) at which F1 values are estimated.
    pitch : numpy.ndarray
        Estimated fundamental frequency (F1) values (Hz).
        Values below 'freqmin' are replaced with NaN.

    """
    # Calculate the window size and hop size based on input parameters
    w_size = int(window_s * tr.stats.sampling_rate)
    hop_size = int(w_size - w_size*overlap)

    # Define the maximum lag for the YIN algorithm
    tau_max = w_size - 1

    # Call the internal _detect_f1 function with specified parameters
    return _detect_f1(
        tr.data, tr.stats.sampling_rate, w_size, tau_max, hop_size, freqmin,
        thresh
    )


def get_harmonics(
    tr, times, pitch, window_s, overlap, n_harmonics_max, window_length_Hz,
    factor, freqmin,
):
    '''
    Detect and characterize harmonics in a time series signal.

    This function analyzes a time series signal to detect and characterize
    harmonic components. It identifies the number of harmonics, their
    frequencies, and their amplitudes within specified parameters.

    Parameters:
    -----------
    tr : ObsPy Trace object
        The time series data to be analyzed.
    times : numpy.ndarray
        Array of time instants corresponding to the signal.
    pitch : numpy.ndarray
        Estimated fundamental frequency (F1) values corresponding to each time
        instant.
    window_s : float
        Duration of the analysis window (seconds).
    overlap : float
        Overlap between consecutive analysis windows (seconds).
    n_harmonics_max : int
        Maximum number of harmonics to detect.
    window_length_Hz : float
        Length of the window (in Hz) used for smoothing the spectrum.
    factor : float
        A scaling factor used to determine peak heights during peak detection.
    freqmin : float
        Minimum frequency (Hz) for identifying harmonics.

    Returns:
    --------
    number : list of int
        Number of the harmonic.
    time : list of UTCDateTime
        Time instants of harmonic detection.
    frequency : list of float
        Detected harmonic frequencies (Hz).
    amplitude : list of float
        Amplitudes of the detected harmonics.
    '''
    # Initialize empty lists to store harmonic information
    number, time, frequency, amplitude = [], [], [], []

    # Find indices with valid pitch estimates (F1)
    pitch_idx = np.argwhere(np.isfinite(pitch))

    # Return empty lists if no valid pitch estimates exist
    if len(pitch_idx) == 0:
        return number, time, frequency, amplitude

    # Determine the start and end indices and times based on valid estimates
    start_idx = pitch_idx.min()
    end_idx = pitch_idx.max()
    start = times[pitch_idx].min() - window_s/2
    end = times[pitch_idx].max() + window_s/2

    # Calculate relative times and trim the trace data
    _times = times - start
    tr.trim(starttime=tr.stats.starttime+start, endtime=tr.stats.starttime+end)
    tr.detrend()

    # Obtain windowed data and apply tapering
    utcdatetimes, data_windowed = st2windowed_data(tr, window_s, overlap)
    data_windowed = data_windowed[0]
    data_windowed = data_windowed.astype(float)
    data_windowed *= tukey(data_windowed.shape[1], alpha=0.1)  # Apply tapering

    # Calculate the frequency domain representation
    freq = np.fft.rfftfreq(data_windowed.shape[1], tr.stats.delta)
    nyquist = tr.stats.sampling_rate/2
    fft_sampling_rate = len(freq)/nyquist  # Samples per Hz
    Sxx = np.abs(rfft(data_windowed))

    # Define the window length for smoothing
    window_length = int(window_length_Hz * fft_sampling_rate)
    if window_length % 2 == 0:
        window_length += 1

    # Iterate through time intervals with valid pitch estimates
    for t, f1, Sx in zip(
        _times[start_idx:end_idx+1],
        pitch[start_idx:end_idx+1],
        Sxx
    ):
        if np.isnan(f1):
            continue

        # Smooth the spectrum
        Sx_smooth = medfilt(Sx, kernel_size=window_length)

        # Calculate the distance for peak detection
        distance = int(f1 * fft_sampling_rate) / 2

        # Find peaks in the spectrum
        peaks, properties = find_peaks(
            Sx,
            height=(factor * Sx_smooth, None),
            distance=distance,
        )

        # Iterate through detected peaks and characterize harmonics
        for i, peak in enumerate(peaks):
            min_f = min(freq[peak], f1)
            max_f = max(freq[peak], f1)
            q = round(max_f / min_f, 0)

            # Check if the detected frequency is within the specified range
            if freq[peak] >= freqmin and q >= 1 and q <= n_harmonics_max:
                number.append(int(q))
                time.append(t)
                frequency.append(freq[peak])
                amplitude.append(properties['peak_heights'][i])

    # Convert time values to UTCDateTime objects
    time = [tr.stats.starttime + t for t in time]

    return number, time, frequency, amplitude


if __name__ == '__main__':
    pass
