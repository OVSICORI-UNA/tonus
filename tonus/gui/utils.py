# Python Standard Library
import json
import logging
import tkinter as tk

# Other dependencies
import matplotlib.pyplot as plt
from obspy import read, Stream

# Local files
from tonus.config import CONF_FILEPATH
from tonus.preprocess import pre_process


def overwrite_c(c):
    with open(CONF_FILEPATH, 'w') as f:
        json.dump(c, f, indent=4)
    tk.messagebox.showinfo(
        'Configuration saved',
        f'Current settings saved in the {CONF_FILEPATH} file'
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
    master.st = Stream()

    master.check_event()

    logging.info('Downloading waveforms...')

    selection = master.frm_waves.station_lbx.curselection()
    station = [master.frm_waves.station_lbx.get(s) for s in selection]

    selection = master.frm_waves.channel_lbx.curselection()
    channel = [master.frm_waves.channel_lbx.get(s) for s in selection]

    if master.c.waveserver.client in 'fdsn earthworm'.split():
        master.st = master.client.get_waveforms(
            master.c.network,
            ','.join(station),
            '--',
            ','.join(channel),
            master.starttime,
            master.endtime,
            # attach_response=True
        )
    elif master.c.waveserver.client == 'files':
        starttime = master.starttime.datetime
        endtime   = master.endtime.datetime
        df = master.df_files
        df = df[
            (df.starttime <= endtime) & (starttime <= df.endtime)
        ]
        df = df[df.station.isin(station)]
        df = df[df.channel.isin(channel)]
        filepaths = df.filepath.unique().tolist()

        if len(filepaths) == 0:
            text = 'None of the files selected contains the requested waveforms'
            tk.messagebox.showwarning('Warning', text)
        else:
            master.st = Stream()
            for filepath in filepaths:
                master.st += read(
                    filepath,
                    starttime=master.starttime,
                    endtime=master.endtime
                )

    if len(master.st) > 0:
        pre_process(master.st, master.inventory)
        logging.info('Stream downloaded and preprocessed.')

    master.st.sort(keys=['station'])
    # Change station/channel options for plotting
    stachas = [
        f'{tr.stats.station} {tr.stats.channel}' for tr in master.st
    ]
    # Initialize the results holder:
    master.results = {}
    for stacha in stachas:
        master.results[stacha] = {}

    master.frm_tr_select.stacha_lbx.delete(0, tk.END)
    for stacha in stachas:
        master.frm_tr_select.stacha_lbx.insert(tk.END, stacha)
    master.frm_tr_select.stacha_lbx.select_set(0)
    master.frm_tr_select.stacha_lbx.event_generate("<<ListboxSelect>>")



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
