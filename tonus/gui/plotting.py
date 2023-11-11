#!/usr/bin/env python


"""
Plotting utilities
"""


# Python Standard Library

# Other dependencies
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from matplotlib import mlab

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'lvmzxc@gmail.com'


def normalize_between_values(a, smin, smax):
    """
    Normalize a NumPy array between two arbitrary values.

    Parameters
    ----------
    a : numpy.ndarray
        The input NumPy array to be normalized.
    smin : float
        The desired minimum value for the normalized and scaled array.
    smax : float
        The desired maximum value for the normalized and scaled array.

    Returns
    -------
    numpy.ndarray
        The normalized and scaled array with values between smin and smax.

    Notes
    -----
    1. finds the minimum and maximum values in the input array 'a'.
    2. normalizes the values in the array to the range [0, 1] and
    3. scales the normalized values to the desired range [smin, smax]
    using a linear transformation.
    """
    # Find the minimum and maximum values in the array
    amin = np.min(a)
    amax = np.max(a)

    # Normalize the array to the range [0, 1]
    anorm = (a - amin) / (amax - amin)

    # Scale the normalized values to the desired range [smin, smax]
    scaled_a = smin + (smax - smin) * anorm

    return scaled_a


def spectrogram(
    c,
    tr,
    ax,
    dbscale=True,
    get_v=True,
):
    nfft = c.spectrogram.nfft
    mult = c.spectrogram.mult
    per_lap = c.spectrogram.per_lap
    ylim = (c.spectrogram.ymin, c.spectrogram.ymax)
    cmap = c.spectrogram.cmap
    std_factor = c.spectrogram.std_factor

    nlap = int(nfft * float(per_lap))

    Sxx, f, t = mlab.specgram(
        tr.data,
        Fs=tr.stats.sampling_rate,
        NFFT=nfft,
        noverlap=nlap,
        pad_to=mult*nfft
    )

    # calculate half bin width
    halfbin_time = (t[1] - t[0]) / 2.0
    halfbin_freq = (f[1] - f[0]) / 2.0
    f = np.concatenate((f, [f[-1] + 2 * halfbin_freq]))
    t = np.concatenate((t, [t[-1] + 2 * halfbin_time]))
    # center bin
    t -= halfbin_time
    f -= halfbin_freq
    if get_v:
        data = np.log(Sxx.flatten())
        data = data[np.isfinite(data)]
        hist, bin_edges = np.histogram(data, bins=100)
        idx = np.argmax(hist)
        mode = (bin_edges[idx] + bin_edges[idx+1])/2
        vmin = mode-std_factor*data.std()
        vmax = mode+std_factor*data.std()
    else:
        vmin = None
        vmax = None

    if dbscale:
        ax.pcolormesh(
            t, f, np.log(Sxx), cmap=cmap, vmin=vmin, vmax=vmax
        )
    else:
        ax.pcolormesh(t, f, (Sxx), cmap=cmap, vmin=vmin, vmax=vmax)

    ax.set_ylim(ylim)
    return


def _plot_db_coda(df, hist):
    fig = plt.figure(figsize=(7, 6.5))
    fig.subplots_adjust(
        left=.1, bottom=.07, right=.9, top=.98, wspace=.2, hspace=.15
    )

    try:
        ax1.remove()
    except Exception as e:
        print(e)
        pass

    rows = 3
    cols = 1

    ax1 = fig.add_subplot(rows, cols, 1)
    ax1.set_ylabel('Frequency [Hz]')

    ax2 = fig.add_subplot(rows, cols, 2, sharex=ax1)
    ax2.set_ylabel('Q')

    # ax3 = fig.add_subplot(rows, cols, 3, sharex=ax1)
    # ax3.set_ylabel('Amplitude [$\mu m/s$]')

    ax4 = fig.add_subplot(rows, cols, 3, sharex=ax1)
    label_fmt = 'Number of events per {}'
    ylabel = label_fmt.format('day')
    if hist.index.freqstr[0] == 'W':
        ylabel = label_fmt.format('week')
    ax4.set_ylabel(ylabel)

    # for ax in [ax1, ax2, ax4]:
    #     ax.axvspan(
    #         datetime.datetime(2021, 6, 13),
    #         datetime.datetime(2022, 8, 13),
    #         facecolor='r',
    #         alpha=0.3,
    #         zorder=-100
    #     )

    # Rincón
    smin, smax = 15, 200
    # # Turrialba
    # smin, smax = 5, 100

    ax4.set_xlim(df.t1.min(), df.t1.max())

    # df = df[~df.isin([np.nan, np.inf, -np.inf]).any(1)]

    for stacha in df.stacha.unique():
        _df = df[df.stacha == stacha]
        _df = _df[_df.amplitude < 1e6]

        # a = _df[['t1', 'event_id', 'amplitude']].groupby('event_id').max()

        # amin = np.log(_df.amplitude.quantile(q=0.05))
        # amax = np.log(_df.amplitude.quantile(q=0.95))
        # s = [(smax-smin)/(amax-amin)*a for a in np.log(_df.amplitude)]

        s = normalize_between_values(_df.amplitude, smin, smax)

        ax1.scatter(
            _df.t1, _df.frequency, label=stacha, lw=0.5, edgecolor='grey', s=s
        )
        ax2.scatter(
            _df.t1, _df.q_f, label=stacha, lw=0.5, edgecolor='grey', s=s
        )
        # ax2.scatter(_df.t1, (_df.t3-_df.t2).dt.total_seconds(),
        #             label=stacha, lw=0.5, edgecolor='grey', s=s)
        # ax3.scatter(_df.t1, _df.amplitude, label=stacha, lw=0.5,
        #            edgecolor='grey', s=s)
        # ax3.scatter(a.t1, a.amplitude, label=stacha, lw=0.5,
        #            edgecolor='grey', s=20)
        # ax3.set_yscale('log')

    # ax4.bar(
    #     hist.index, hist.n, edgecolor='gray', linewidth=0.5,
    #     width=2
    # )
    ax4.plot(hist.index, hist.n)
    ax2.set_yscale('log')

    # RINCON DE LA VIEJA EJEMPLO
    # ax1.set_ylim(5.18, 8.5)

    # Turrialba
    # ax1.set_ylim(5., 6)
    # ax2.set_ylim(1, 9000)

    for ax in fig.get_axes():
        ax.grid('on', alpha=0.5)
    ax2.legend()

    return fig


def _plot_db_tremor(df, hist):
    s = 25

    fig = plt.figure(figsize=(6.5, 7.5))
    fig.subplots_adjust(
        left=.1,
        bottom=.06,
        right=.95,
        top=.98, wspace=.2,
        hspace=.26
    )

    try:
        ax1.remove()
    except Exception as e:
        print(e)
        pass

    rows = 5
    cols = 1

    ax1 = fig.add_subplot(rows, cols, 1)
    ax1.set_ylabel('Fundamental\nfrequency [Hz]')

    ax2 = fig.add_subplot(rows, cols, 2, sharex=ax1)
    ax2.set_ylabel(r'Amplitude [$\mu m/s$]')

    ax3 = fig.add_subplot(rows, cols, 3, sharex=ax1)
    ax3.set_ylabel('Duration [s]')

    ax4 = fig.add_subplot(rows, cols, 5, sharex=ax1)

    ax5 = fig.add_subplot(rows, cols, 4, sharex=ax1)
    ax5.set_ylabel('Number of\nharmonics')

    label_fmt = 'Number of events\nper {}'
    ylabel = label_fmt.format('day')
    bin_width = 1
    if hist.index.freqstr[0] == 'W':
        ylabel = label_fmt.format('week')
        bin_width = 7
    ax4.set_ylabel(ylabel)

    def scatter(ax, x, y, label):
        ax.scatter(x, y, label=label, lw=0.25, edgecolor='r', s=s)

    for stacha in df.stacha.unique():

        _df = df[df.stacha == stacha]

        duration = (_df.endtime - _df.starttime).dt.total_seconds()

        scatter(ax1, _df.starttime, _df.fmean, stacha)
        scatter(ax2, _df.starttime, _df.amplitude*1e6, stacha)
        scatter(ax3, _df.starttime, duration, stacha)
        scatter(ax5, _df.starttime, _df.n_harmonics, stacha)

    ax4.bar(
        hist.index,
        hist.n,
        edgecolor='r',
        linewidth=0.25,
        width=pd.Timedelta(days=bin_width),
    )

    ax2.set_ylim(0.05, 20)
    ax2.set_yscale('log')

    # Ejemplo Turrialba
    # import datetime
    # import matplotlib.dates as md
    # ax1.set_ylim(0.5, 3.1)
    # ax3.set_ylim(-300, 4000)
    # ax4.set_xlim(
    #     datetime.datetime(2018, 2, 1),
    #     datetime.datetime(2018, 12, 1)
    # )
    # for ax in fig.get_axes():
    #     ax.xaxis.set_major_locator(md.MonthLocator(interval=2))
    #     ax.xaxis.set_minor_locator(md.DayLocator(interval=7))
    return fig


def plot_db(df, hist, event_type):
    if event_type == 'coda':
        return _plot_db_coda(df, hist)
    elif event_type == 'tremor':
        return _plot_db_tremor(df, hist)


if __name__ == '__main__':
    pass
