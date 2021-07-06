from obspy import Trace, Stream
from scipy.signal import butter, lfilter


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


def preprocess(st, freqmin, freqmax, order):
    st.detrend()
    butter_bandpass_filter(st, freqmin, freqmax, order)
