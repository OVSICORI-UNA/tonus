#!/usr/bin/env python


"""
Coda analysis module

This module provides functions for coda data analysis, focusing on
spectral analysis and peak detection.

"""


# Python Standard Library

# Other dependencies
import numpy as np

from scipy.signal import find_peaks, medfilt
from scipy.stats import linregress

from tonus.preprocess import butter_bandpass_filter

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'lvmzxc@gmail.com'


def peak_width_half_abs_height(freq, fft, peak):
    """
    We search the samples that sourround the half energy level,
    the subscripts are for left and right, 1st subscript refers to the
    side of the spectrum relative to the peak, the 2nd subscript refers
    to the side relative to the half energy level.
    Then the frequency at the half energy level is obtained by
    interpolation.

                            peak

                   idx_lr          idx_rl

           ------------ half energy level ------------

               idx_ll                     idx_rr

    Parameters
    ----------
    freq : numpy.ndarray
        1D array containing the frequency values.

    fft : numpy.ndarray
        1D array containing the magnitude values of the FFT spectrum.

    peak : int
        Index of the peak in the 'freq' and 'fft' arrays

    Returns
    -------
    freq_left : float
        Frequency at the left boundary of the half-height range of the peak.

    freq_right : float
        Frequency at the right boundary of the half-height range of the peak.
    """

    # Slice from peak to the left
    fft_left = np.flip(fft[:peak+1], axis=0)
    freq_left = np.flip(freq[:peak+1], axis=0)

    i = 0
    while fft_left[i] >= fft[peak]/2:
        idx_lr = i
        i += 1
    idx_ll = i

    f_ll = freq_left[idx_ll]
    f_lr = freq_left[idx_lr]

    e_ll = fft_left[idx_ll]
    e_lr = fft_left[idx_lr]

    freq_left = ((fft[peak]/2 - e_ll)*(f_lr - f_ll))/(e_lr - e_ll) + f_ll

    # Slice from peak to the right
    fft_right = fft[peak:]
    freq_right = freq[peak:]

    i = 0
    while fft_right[i] >= fft[peak]/2:
        idx_rl = i
        i += 1
    idx_rr = i

    f_rl = freq_right[idx_rl]
    f_rr = freq_right[idx_rr]

    e_rl = fft_right[idx_rl]
    e_rr = fft_right[idx_rr]

    freq_right = ((fft[peak]/2 - e_rl)*(f_rr - f_rl))/(e_rr - e_rl) + f_rl

    return freq_left, freq_right


def get_peaks(
    tr,
    freqmin,
    freqmax,
    order,
    factor,
    distance_Hz=0.3,
    prominence_min=0.04,
    window_length_Hz=3
):
    """
    Analyzes a time series signal to detect and characterize peaks in its
    frequency spectrum and perform related calculations.

    Parameters:
    -----------
    tr : ObsPy Trace object
        The time series data to be analyzed.

    freqmin : float
        The minimum frequency (in Hz) for the bandpass filter.

    freqmax : float
        The maximum frequency (in Hz) for the bandpass filter.

    order : int
        The order of the bandpass filter.

    factor : float
        A scaling factor used to determine peak heights.

    distance_Hz : float, optional (default=0.3)
        The minimum horizontal distance between detected peaks in the frequency
        domain, in Hz.

    prominence_min : float, optional (default=0.04)
        Minimum prominence required for a peak to be considered.

    window_length_Hz : float, optional (default=3)
        The length of the window (in Hz) used for smoothing the spectrum.

    Returns:
    --------
    freq : numpy.ndarray
        Array of frequencies corresponding to the detected peaks.

    fft_norm : numpy.ndarray
        Normalized magnitude spectrum of the input signal.

    fft_smooth : numpy.ndarray
        Smoothed version of the magnitude spectrum.

    peaks : list
        List of indices corresponding to the detected peaks in the magnitude
        spectrum.

    f : numpy.ndarray
        Frequencies at which peaks were detected.

    a : numpy.ndarray
        Amplitudes of the detected peaks, in micrometers per second.

    q_f : list
        Quality factors (Q) calculated based on peak width at half-maximum.

    q_alpha : float
        Quality factor (Q) calculated based on the alpha parameter.

    """
    # Pre-process
    tr.detrend()
    butter_bandpass_filter(tr, freqmin, freqmax, order)

    # Compute FFT
    freq = np.fft.rfftfreq(tr.stats.npts, tr.stats.delta)
    fft = np.abs(np.fft.rfft(tr.data))

    # Normalize to make parameters standard
    fft_norm = fft.copy()/fft.max()

    # Get samples per Hz
    nyquist = tr.stats.sampling_rate/2
    fft_sampling_rate = len(fft)/nyquist  # Samples per Hz

    # Convert parameters: Hz to samples
    distance = distance_Hz * fft_sampling_rate  # Samples / Hz * Hz
    if distance < 1:
        distance = 1

    window_length = int(window_length_Hz * fft_sampling_rate)
    if window_length % 2 == 0:
        window_length += 1

    # Smooth FFT
    fft_smooth = medfilt(fft_norm, kernel_size=window_length)

    # Find peaks
    peaks, properties = find_peaks(
        fft_norm,
        height=(factor*fft_smooth, None),
        distance=distance,
        prominence=(prominence_min, None)
    )

    if len(peaks) == 0:
        return freq, fft_norm, fft_smooth, [], [], [], [], []

    f = freq[peaks]
    a = fft[peaks]*1e6

    # Q = f/deltaF
    q_f = []
    for peak in peaks:
        freq_left, freq_right = peak_width_half_abs_height(freq, fft, peak)
        q_f.append(freq[peak]/(freq_right-freq_left))

    # Q = pi*f/alpha
    # alpha = pi*f/Q
    time, amplitude = [], []
    for window in tr.slide(window_length=2, step=1):
        amplitude.append(np.sqrt(np.mean(window.data**2)))
        win_time = (window.stats.starttime - tr.stats.starttime)
        time.append(win_time)
    time = np.asarray(time)
    amplitude = np.asarray(amplitude)
    slope, intercept, r_value, p_value, std_err = linregress(
        time, np.log(amplitude)
    )
    # f_dom = f[fft[peaks].argmax()]
    f_1 = f[0]
    # q_alpha = (np.pi*f_dom)/-slope
    q_alpha = (np.pi*f_1)/-slope

    return freq, fft_norm, fft_smooth, peaks, f, a, q_f, q_alpha


if __name__ == '__main__':
    pass
