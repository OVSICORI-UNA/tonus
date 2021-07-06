# Python Standard Library

# Other dependencies
from numba import jit
import numpy as np
import pandas as pd
from scipy.fft import rfft
from scipy.signal.windows import tukey

# Local files
from tonus.detection.obspy2numpy import st2windowed_data


@jit(nopython=True)
def _get_cft(Sxx, k, _bin_width):
    cft = np.zeros(len(Sxx), dtype=np.float64)
    for j, Sx in enumerate(Sxx):
        index = np.argsort(-Sx)
        c, effective = 0, []
        for i, idx in enumerate(index):
            nxt = False
            if i > 0:
                for e in effective:
                    if (idx < e+_bin_width/2) and (idx > e-_bin_width/2):
                        nxt = True
                        break
            if nxt:
                continue

            if len(effective) >= k:
                break

            left  = int(idx - _bin_width/2)
            right = int(idx + _bin_width/2)

            left_pad, right_pad = 0, 0

            if left < 0:
                left_pad = -1*left
                left = 0

            if right >= len(Sx):
                right_pad = right - len(Sx) + 1
                right = len(Sx) - 1

            Sx_slice = np.zeros(_bin_width, dtype=np.float64)

            Sx_slice[left_pad:left_pad+right-left] = Sx[left:right]

            if left_pad != 0:
                Sx_slice[:left_pad]  = np.median(Sx[left:right])
            if right_pad != 0:
                Sx_slice[-right_pad:] = np.median(Sx[left:right])

            Sx_slice = Sx_slice/Sx_slice.max()

            med = np.median(Sx_slice)

            c += (1/med)
            effective.append(idx)
        cft[j] = c
    return cft


def get_cft(tr, short_win, overlap, pad, k, bin_width, long_win):
    utcdatetimes, data_windowed = st2windowed_data(tr, short_win, overlap)

    data_windowed  = data_windowed[0]
    data_windowed  = data_windowed.astype(float)
    data_windowed *= tukey(data_windowed.shape[1], alpha=pad) # taper

    freq = np.fft.rfftfreq(data_windowed.shape[1], tr.stats.delta)

    nyquist = tr.stats.sampling_rate/2
    fft_sampling_rate = len(freq)/nyquist # Samples per Hz
    _bin_width = int(bin_width*fft_sampling_rate)

    Sxx = np.abs(rfft(data_windowed))
    cft = _get_cft(Sxx, k, _bin_width)

    delta = short_win - overlap*short_win
    _long_win = int(long_win/delta)

    cf = pd.Series(cft)
    cft = cf / cf.rolling(_long_win).mean()
    cft = cft.to_numpy()

    tr.data = cft
    tr.stats.delta = delta
    tr.stats.starttime = utcdatetimes[0]
    return
