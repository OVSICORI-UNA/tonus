# Python Standard Library

# Other dependencies
from matplotlib import mlab
import matplotlib.pyplot as plt
import numpy as np

# Local files


def spectrogram(c,
    tr, ax,
    dbscale=True,
    get_v=True,
):
    nfft       = c.spectrogram.nfft
    mult       = c.spectrogram.mult
    per_lap    = c.spectrogram.per_lap
    ylim       = (c.spectrogram.ymin, c.spectrogram.ymax)
    cmap       = c.spectrogram.cmap
    std_factor = c.spectrogram.std_factor

    nlap = int(nfft * float(per_lap))

    Sxx, f, t = mlab.specgram(tr.data, Fs=tr.stats.sampling_rate, NFFT=nfft,
                              noverlap=nlap, pad_to=mult * nfft)

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
        specgram = ax.pcolormesh(
            t, f, np.log(Sxx), cmap=cmap, vmin=vmin, vmax=vmax
        )
    else:
        specgram = ax.pcolormesh(t, f, (Sxx), cmap=cmap, vmin=vmin, vmax=vmax)

    ax.set_ylim(ylim)
    return


def _plot_db_coda(df, hist):
    fig = plt.figure(figsize=(6, 6.5))
    fig.subplots_adjust(left=.1, bottom=.07, right=.9, top=.98,
                        wspace=.2, hspace=.15)
    try:
        ax1.remove()
    except:
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
    ax4.set_ylabel('Number of daily events')

    smin, smax = 20, 50
    alpha = 0.5

    df = df[~df.isin([np.nan, np.inf, -np.inf]).any(1)]


    for stacha in df.stacha.unique():
        _df = df[df.stacha == stacha]
        _df = _df[_df.amplitude < 1e6]

        a = _df[['t1', 'event_id', 'amplitude']].groupby('event_id').max()

        s = 25

        # amin = np.log(_df.amplitude.min())
        # amax = np.log(_df.amplitude.max())
        # s = [(smax-smin)/(amax-amin)*a for a in np.log(_df.amplitude)]

        amin = _df.amplitude.min()
        amax = _df.amplitude.max()
        s = [a*(smax-smin)/(amax-amin) for a in _df.amplitude]


        ax1.scatter(_df.t1, _df.frequency, label=stacha, lw=0.5,
                    edgecolor='grey', s=s)
        ax2.scatter(_df.t1, _df.q_f, label=stacha, lw=0.5,
                   edgecolor='grey', s=s)
        # ax2.scatter(_df.t1, (_df.t3-_df.t2).dt.total_seconds(),
        #             label=stacha, lw=0.5, edgecolor='grey', s=s)
        # ax3.scatter(_df.t1, _df.amplitude, label=stacha, lw=0.5,
        #            edgecolor='grey', s=s)
        # ax3.scatter(a.t1, a.amplitude, label=stacha, lw=0.5,
        #            edgecolor='grey', s=20)
        # ax3.set_yscale('log')

    ax4.bar(hist.index, hist.n, edgecolor='gray', linewidth=0.5)

    # RINCON DE LA VIEJA EJEMPLO
    # from datetime import datetime
    # import matplotlib.dates as md

    # ax4.set_xlim(datetime(2019, 11, 16), datetime(2020, 3, 15))
    # ax1.set_ylim(6, 8.5)

    # for ax in fig.get_axes():
    #     ax.xaxis.set_major_locator(md.DayLocator(interval=21))
    #     ax.xaxis.set_minor_locator(md.DayLocator(interval=7))

    for ax in fig.get_axes():
        ax.grid('on', alpha=alpha)
    ax2.legend()

    return fig


def _plot_db_tremor(df, hist):
    s = 25

    fig = plt.figure(figsize=(6, 6.5))
    fig.subplots_adjust(left=.1, bottom=.07, right=.9, top=.98,
                        wspace=.2, hspace=.15)
    try:
        ax1.remove()
    except:
        pass

    rows = 4
    cols = 1

    ax1 = fig.add_subplot(rows, cols, 1)
    ax1.set_ylabel('Fundamental\nfrequency [Hz]')

    ax2 = fig.add_subplot(rows, cols, 2)
    ax2.set_ylabel('Number of harmonics')

    ax3 = fig.add_subplot(rows, cols, 3)
    ax3.set_ylabel('Amplitude [m/s]')

    ax4 = fig.add_subplot(rows, cols, 4)
    ax4.set_ylabel('Duration')

    for stacha in df.stacha.unique():
        _df = df[df.stacha == stacha]

        ax1.scatter(
            _df.starttime,
            _df.fmean,
            label=stacha,
            lw=0.5,
            edgecolor='grey',
            s=s
        )
        ax2.scatter(
            _df.starttime,
            _df.n_harmonics,
            label=stacha,
            lw=0.5,
            edgecolor='grey',
            s=s
        )
        ax3.scatter(
            _df.starttime,
            _df.amplitude,
            label=stacha,
            lw=0.5,
            edgecolor='grey',
            s=s
        )
        ax4.scatter(
            _df.starttime,
            (_df.endtime - _df.starttime).dt.total_seconds(),
            label=stacha,
            lw=0.5,
            edgecolor='grey',
            s=s
        )
    return fig

def plot_db(df, hist, event_type):
    if event_type == 'coda':
        return _plot_db_coda(df, hist)
    elif event_type == 'tremor':
        return _plot_db_tremor(df, hist)

