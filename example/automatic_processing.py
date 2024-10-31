#!/usr/bin/env python


"""
"""


# Python Standard Library
import argparse
import os

# Other dependencies
import matplotlib.dates as md
import matplotlib.pyplot as plt
import obspy
import pandas as pd
import tonus

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'lvmzxc@gmail.com'


plt.style.use('default')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', help='input csv file',)
    return parser.parse_args()


def main():
    args = parse_args()

    df = pd.read_csv(args.filepath, names=['starttime', 'label', 'duration'])

    c = tonus.config.set_conf()
    inventory = obspy.read_inventory(c.inventory)

    st = obspy.Stream()
    for filename in os.listdir(c.detect.io.input_dir):
        filepath = os.path.join(c.detect.io.input_dir, filename)
        try:
            st += obspy.read(filepath)
        except Exception as e:
            print(e)

    data = []
    for i, row in df.iterrows():
        starttime = obspy.UTCDateTime(row.starttime)
        endtime = starttime + row.duration
        _st = st.copy().trim(starttime, endtime)
        tonus.preprocess.pre_process(_st, inventory)

        for tr in _st:
            (
                freq,
                fft_norm,
                fft_smooth,
                peaks,
                f,
                a,
                q_f,
                q_alpha
            ) = tonus.process.coda.get_peaks(tr, 3, 10, 4, 3,)

            for j, p in enumerate(peaks):
                data.append(
                    dict(
                        t=starttime.datetime,
                        frequency=f[j],
                        amplitude=a[j],
                        station=tr.stats.station
                    )
                )

    out = pd.DataFrame(data)

    stations = [tr.stats.station for tr in st]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_ylabel('Frequency [Hz]')
    ax.set_yscale('log')
    ax.legend()
    ax.xaxis.set_major_locator(md.HourLocator(interval=2))
    ax.xaxis.set_major_formatter(md.DateFormatter('%H:%M'))
    ax.set_xlabel(st[0].stats.starttime.date)

    out['s'] = out.amplitude/2
    for station in stations:
        _out = out[out.station == station]
        ax.scatter(
            _out.t,
            _out.frequency,
            label=station,
            s=_out.s,
            lw=0.5,
            ec='k',
            alpha=0.5,
        )

    fig.tight_layout()
    fig.savefig('results.png', dpi=250)
    return


if __name__ == '__main__':
    main()
