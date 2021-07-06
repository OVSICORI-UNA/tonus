# -*- coding: utf-8 -*-
"""Creates windowed array from ObsPy Stream or Trace objects
This module offers a function to replace the for loop:
>>> for window in st.slide(window_length, step):
>>>        window...
This for loop is easy and intuitive to use but slow for large dataset
Instead use:
>>> utcdatetime, data_windowed = st2windowed_data(st, window_length, overlap)
utcdatetime contains the UTCDateTime object for each window center
data_windowed is an array with shape: (n_traces, n_windows, window_pts)
"""
import numpy as np
from obspy import Stream, Trace
from obspy.core.util.misc import get_window_times
from skimage.util.shape import view_as_windows


def st2windowed_data(st, window_length, overlap):
    """Creates overlapping windowed data from obspy Stream object
    Depends on skimage.util.shape.view_as_windows
    You can pass either a Trace or a Stream
    Parameters
    ----------
    st : obspy Stream or Trace object
        Stream with n number of traces (n_traces),
        also a single Trace can be given
    window_length : int
        Window length in seconds
    overlap : float
        Window percentage of overlap, float form 0 to 1
    Returns
    -------
    time : np 1D array
        Contains the UTCDateTime object for each window center
    data_windowed : np ndarray
        Array with shape: (n_traces, n_windows, window_pts)
    """
    if isinstance(st, Trace):
        st = Stream(traces=[st])

    # TODO check that all traces have same sampling rate, if not, upsample to
    # the maximum

    starttimes = [tr.stats.starttime for tr in st]
    endtimes = [tr.stats.endtime for tr in st]
    st.trim(starttime=max(starttimes), endtime=min(endtimes))

    utcdatetime = get_window_times(st[0].stats.starttime, st[0].stats.endtime,
                                   window_length=window_length,
                                   step=window_length - window_length*overlap,
                                   offset=0, include_partial_windows=False)
    utcdatetime = (np.array(utcdatetime)[:, :1]+window_length/2).flatten()

    # Stream -> array of shape: (n_traces, npts)
    n_traces = len(st)
    data = np.array([tr.data for tr in st])

    # Convert to point units
    window_pts  = int(window_length * st[0].stats.sampling_rate)
    overlap_pts = int(window_pts * overlap)
    step        = window_pts - overlap_pts

    # Get number of total complete windows
    window_ends_idx = np.arange(window_pts - 1, data.shape[1], step)
    n_windows = len(window_ends_idx)

    # Trim to fit number of complete windows
    data = data[:, :window_ends_idx[-1]+1]

    data_windowed = view_as_windows(
        arr_in=data, window_shape=(n_traces, window_pts), step=step
    )[0]

    data_windowed = np.transpose(data_windowed, axes=[1, 0, 2])

    return utcdatetime, data_windowed
