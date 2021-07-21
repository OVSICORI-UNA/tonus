# Python Standard Library

# Other dependencies
import numpy as np
from numba import jit
from scipy.fft import rfft
from scipy.signal import find_peaks, medfilt
from scipy.signal.windows import tukey

# Local files
from tonus.detection.obspy2numpy import st2windowed_data


@jit(nopython=True)
def yin_block(data, fs, w_size, tau_max, thresh):
    '''
    Returns a pitch estimate for a windowed chunk of signal
    '''
    ## difference function (autocorrelation-like)
    r = np.zeros(tau_max)
    for i in range(tau_max):
        vec = np.zeros(w_size, dtype=np.float64)
        vec[:] = data[:w_size] - data[i:w_size+i]
        r[i] = np.dot(vec, vec)

    ## d calculation
    d = np.zeros(tau_max)
    s = r[0]
    d[0] = 1
    for i in range(1, tau_max):
        s += r[i]
        d[i] = r[i] / ((1/i)*s)

    ## pick minimum (first min below threshold)
    idcs = np.where(d < thresh)
    if len(d[idcs]) == 0:
        return np.nan, np.nan
    return min(d[idcs]), fs/idcs[0][np.argmin(d[idcs])]


def _detect_f1(data, fs, w_size, tau_max, hop_size, freqmin, thresh):
    num_hops = (len(data) - w_size - tau_max)//(hop_size) + 1
    pitch = np.zeros(num_hops)
    tau = np.zeros(num_hops)
    idx0 = 0
    idx1 = idx0 + w_size + tau_max
    for n in range(num_hops):
        c, p = yin_block(
            data[idx0:idx1], fs, w_size, tau_max, thresh
        )
        if p > freqmin:
            pitch[n] = p
            tau[n] = c
        else:
            pitch[n] = np.nan
            tau[n] = np.nan
        idx0 += hop_size
        idx1 += hop_size
    time_hop = hop_size/fs
    t = np.linspace(0, time_hop*num_hops, num_hops)
    t += time_hop/2
    return tau, t, pitch


def detect_f1(tr, window_s, overlap, freqmin, thresh):
    w_size   = int(window_s * tr.stats.sampling_rate)
    hop_size = int(w_size - w_size*overlap)
    tau_max  = w_size - 1
    return _detect_f1(
        tr.data, tr.stats.sampling_rate, w_size, tau_max, hop_size, freqmin,
        thresh
    )


def get_harmonics(
    tr, times, pitch, window_s, overlap, n_harmonics_max, window_length_Hz,
    factor, freqmin,
):
    number, time, frequency, amplitude = [], [], [], []

    pitch_idx = np.argwhere(np.isfinite(pitch))
    if len(pitch_idx) == 0:
        return number, time, frequency, amplitude

    start_idx = pitch_idx.min()
    end_idx = pitch_idx.max()

    start = times[pitch_idx].min() - window_s/2
    # end   = times[pitch_idx+1].max() + window_s/2
    end   = times[pitch_idx].max() + window_s/2

    _times = times - start

    tr.trim(starttime=tr.stats.starttime+start, endtime=tr.stats.starttime+end)
    tr.detrend()
    # tr.filter('bandpass', freqmin=freqmin, freqmax=tr.stats.sampling_rate/2-0.1)

    utcdatetimes, data_windowed = st2windowed_data(tr, window_s, overlap)

    data_windowed  = data_windowed[0]
    data_windowed  = data_windowed.astype(float)
    data_windowed *= tukey(data_windowed.shape[1], alpha=0.1) # taper

    freq = np.fft.rfftfreq(data_windowed.shape[1], tr.stats.delta)

    nyquist = tr.stats.sampling_rate/2
    fft_sampling_rate = len(freq)/nyquist # Samples per Hz

    Sxx = np.abs(rfft(data_windowed))

    window_length = int(window_length_Hz * fft_sampling_rate)
    if window_length%2 == 0:
        window_length += 1

    for t, f1, Sx in zip(
        _times[start_idx:end_idx+1], pitch[start_idx: end_idx+1], Sxx
    ):
        if np.isnan(f1):
            continue
        Sx_smooth = medfilt(Sx, kernel_size=window_length)

        distance = int(f1*fft_sampling_rate)/2

        peaks, properties = find_peaks(
            Sx,
            height=(factor*Sx_smooth, None),
            distance=distance,
        )

        for i, peak in enumerate(peaks):
            min_f = min(freq[peak], f1)
            max_f = max(freq[peak], f1)
            q = round(max_f/min_f, 0)
            r = max_f - q*min_f
            if freq[peak] >= freqmin and q >= 1 and q <= n_harmonics_max:
                number.append(int(q))
                time.append(t)
                frequency.append(freq[peak])
                amplitude.append(properties['peak_heights'][i])

    time = [tr.stats.starttime+t for t in time]
    return number, time, frequency, amplitude



