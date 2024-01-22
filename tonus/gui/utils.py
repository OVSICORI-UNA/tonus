#!/usr/bin/env python


"""
Various and diverse utils.
"""


# Python Standard Library
import logging
import tkinter as tk
import tomllib

# Other dependencies
import matplotlib.pyplot as plt
import tonus

from obspy import read, Stream

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'lvmzxc@gmail.com'


def overwrite_c(c):
    with open(tonus.config.CONF_FILEPATH, 'w') as f:
        tomllib.dump(c, f)
    tk.messagebox.showinfo(
        'Configuration saved',
        f'Current settings saved in the {tonus.config.CONF_FILEPATH} file'
    )


def isfloat(what):
    if what == '':
        return True
    try:
        float(what)
        return True
    except ValueError:
        return False


def open_window(master, window):
    window.transient(master)
    window.grab_set()
    master.wait_window(window)
    master.focus_force()


def download(master):
    """
    Downloads seismic waveforms based on user-selected parameters and
    stores them in 'master.st'.

    Parameters:
    -----------
    master : tk.Toplevel
        The application window
        (tonus.gui.coda.AppCoda or tonus.gui.tremor.AppTremor)
        containing configuration and user selections.

    Returns:
    --------
    None
    """
    # Initialize the stream to store downloaded waveforms
    master.st = Stream()

    # Check if an event is in the database for this volcano
    master.check_event()

    logging.info('Downloading waveforms...')

    # Get selected stations and channels for download
    selection = master.frm_waves.station_lbx.curselection()
    station = [master.frm_waves.station_lbx.get(s) for s in selection]

    selection = master.frm_waves.channel_lbx.curselection()
    channel = [master.frm_waves.channel_lbx.get(s) for s in selection]

    # Download waveforms from FDSN or Earthworm server
    if master.c.waveserver.name in 'fdsn earthworm'.split():
        try:
            master.st = master.client.get_waveforms(
                master.c.network,
                ','.join(station),
                '--',
                ','.join(channel),
                master.starttime,
                master.endtime,
                attach_response=False
            )
        except Exception as e:
            tk.messagebox.showwarning('Warning', e)
    # Download waveforms from files source
    elif master.c.waveserver.name == 'files':
        starttime = master.starttime.datetime
        endtime = master.endtime.datetime
        try:
            df = master.df_files
        except Exception:
            text = 'No waveform files pre-loaded, go back to launch window.'
            tk.messagebox.showwarning('Warning', text)
            return

        df = df[(df.starttime <= endtime) & (starttime <= df.endtime)]
        df = df[df.station.isin(station)]
        df = df[df.channel.isin(channel)]
        filepaths = df.filepath.unique().tolist()

        if len(filepaths) == 0:
            text = 'None of the selected files contain the requested waves'
            tk.messagebox.showwarning('Warning', text)
        else:
            # Initialize an empty stream to store the loaded waveforms
            master.st = Stream()
            for filepath in filepaths:
                master.st += read(
                    filepath,
                    starttime=master.starttime,
                    endtime=master.endtime
                )

    # Preprocess the downloaded waveforms and log completion
    if len(master.st) > 0:
        tonus.preprocess.pre_process(master.st, master.inventory)
        logging.info('Stream downloaded and preprocessed.')

    # Sort the stream by station
    master.st.sort(keys=['station'])

    # Get station/channels paris
    stachas = [f'{tr.stats.station} {tr.stats.channel}' for tr in master.st]

    # Initialize the results holder for each station/channel combination
    master.results = {}
    for stacha in stachas:
        master.results[stacha] = {}

    # Update the station/channel selection listbox
    master.frm_tr_select.stacha_lbx.delete(0, tk.END)
    for stacha in stachas:
        master.frm_tr_select.stacha_lbx.insert(tk.END, stacha)
    master.frm_tr_select.stacha_lbx.select_set(0)
    master.frm_tr_select.stacha_lbx.event_generate('<<ListboxSelect>>')
    return


def select_trace(master):
    selection = master.frm_tr_select.stacha_lbx.curselection()
    if len(selection) < 1:
        return
    stacha = master.frm_tr_select.stacha_lbx.get(selection[0])
    station, channel = stacha.split()
    master.tr = master.st.select(station=station, channel=channel)[0]
    plt.close()
    master.plot()


class Table:
    def __init__(self, master, header, columns):
        font_size = 12
        width = 15

        for column, head in enumerate(header):
            self.e = tk.Entry(master, width=width)
            self.e.grid(row=0, column=column)
            self.e.insert(tk.END, head)
            self.e.config(
                state='disabled',
                disabledforeground='black',
                font=f'Arial {font_size} bold'
            )

        for column, data in enumerate(columns):
            for row, datum in enumerate(data):
                self.e = tk.Entry(master, width=width)
                self.e.grid(row=row+1, column=column)
                self.e.insert(tk.END, datum)
                self.e.config(
                    state='disabled',
                    disabledforeground='black',
                    font=f'Arial {font_size}'
                )


if __name__ == '__main__':
    pass
