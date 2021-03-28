import numpy as np
from obspy import UTCDateTime, Trace, Stream
from scipy.signal import butter, find_peaks, lfilter, savgol_filter
from scipy.stats import linregress


def _butter_bandpass_filter(tr, freqmin, freqmax, order):
    """Filter a obspy Trace with a Butterworth filter

    Relies on scipy.signal butter and lfilter functions
    Detrending must be performed calling this function.
    This functions alter permanently the Trace data

    Parameters
    ----------
    tr : obspy.core.trace object
        Will be modified, must do a copy before if you want.
    freqmin : float
        Lower frequency
    freqmax : float
        Higher frequency
    order : int
        Filter order

    Returns
    -------
    """
    nyquist = .5 * tr.stats.sampling_rate
    low     = freqmin / nyquist
    high    = freqmax / nyquist
    b, a    = butter(order, [low, high], btype='band')
    tr.data = lfilter(b, a, tr.data)
    return


def butter_bandpass_filter(st, freqmin, freqmax, order):
    if isinstance(st, Trace):
        _butter_bandpass_filter(st, freqmin, freqmax, order)
    elif isinstance(st, Stream):
        for tr in st:
            _butter_bandpass_filter(tr, freqmin, freqmax, order)


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
    freq : np 1d array
    fft : np 1d array
    peak : index of the peak in freq and fft
    Returns
    -------
    freq_left : float
    freq_right : float
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
        idx_rl =  i
        i += 1
    idx_rr = i

    f_rl = freq_right[idx_rl]
    f_rr = freq_right[idx_rr]

    e_rl = fft_right[idx_rl]
    e_rr = fft_right[idx_rr]

    freq_right = ((fft[peak]/2 - e_rl)*(f_rr - f_rl))/(e_rr -e_rl) + f_rl

    width = freq_right - freq_left
    return freq_left, freq_right


def get_peaks(tr, freqmin, freqmax, order, factor, distance_Hz=0.3,
              prominence_min=0.04, threshold=0.01, window_length_Hz=3):

    # Pre-process
    tr.detrend()
    tr_copy = tr.copy()
    butter_bandpass_filter(tr, freqmin, freqmax, order)
    # tr.trim(starttime=t2, endtime=t3)

    # Compute FFT
    freq = np.fft.rfftfreq(tr.stats.npts, tr.stats.delta)
    fft  = np.abs(np.fft.rfft(tr.data))

    # Normalize to make parameters standard
    fft_norm = fft.copy()/fft.max()

    # Get samples per Hz 
    nyquist = tr.stats.sampling_rate/2
    fft_sampling_rate = len(fft)/nyquist # Samples per Hz

    # Convert parameters: Hz to samples
    distance = distance_Hz * fft_sampling_rate # Samples / Hz * Hz 
    if distance < 1:
        distance = 1

    window_length = int(window_length_Hz * fft_sampling_rate)
    if window_length%2 == 0:
        window_length += 1

    # Smooth FFT
    fft_smooth = savgol_filter(fft_norm, window_length=window_length,
                               polyorder=1)
    # Find peaks
    peaks, properties = find_peaks(fft_norm, height=(factor*fft_smooth, None),
                                   distance=distance,
                                   prominence=(prominence_min, None))

    if len(peaks) == 0:
        return freq, fft_norm, fft_smooth, [], [], [], [], []

    f = freq[peaks]
    a = fft[peaks]

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
        win_time = (window.stats.starttime-tr.stats.starttime)
        time.append(win_time)
    time = np.asarray(time)
    amplitude = np.asarray(amplitude)
    slope, intercept, r_value, p_value, std_err = linregress(
        time, np.log(amplitude)
    )
    # f_dom = f[fft[peaks].argmax()]
    f_1   = f[0]
    # q_alpha = (np.pi*f_dom)/-slope
    q_alpha = (np.pi*f_1)/-slope

    return freq, fft_norm, fft_smooth, peaks, f, a, q_f, q_alpha
