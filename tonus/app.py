#!/usr/bin/env python

# Python Standard Library
from datetime import datetime, timedelta
import json
import logging
import tkinter as tk
import sys

# Other dependencies
import matplotlib.pyplot as plt
from matplotlib import mlab
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)
from matplotlib.backend_bases import key_press_handler
from matplotlib.widgets import MultiCursor
import numpy as np
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
import pandas as pd
import psycopg2

# Local files
from tonus.config import set_conf, CONF_FILEPATH
from tonus.process import get_peaks


logging.basicConfig(level=logging.INFO)

plt.style.use('dark_background')
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['keymap.home'] = 'r'
plt.rcParams['keymap.zoom'] = 'd'


class Root(tk.Tk):
    def __init__(self):
        super().__init__()

        self._set_conf()

        self.wm_title('tonus')

        # Style
        self.font_title = 'Helvetica 14 bold'
        self.bd = 1
        self.relief = tk.GROOVE

        try:
            # FDSN start-up connection
            self.client = self.connect_waveserver(
                self.c.fdsn.ip, self.c.fdsn.port
            )

            # Connect to database
            self.conn = psycopg2.connect(**self.c.db)
            logging.info('Succesfully connected to the database.')

        except Exception as e:
            print(e)
            sys.exit(1)

        # Menu bar
        self.menubar = self.FrameMenu(self)

        # Frames initiation
        self.frm_waves   = self.FrameWaves(self)
        self.frm_plt_p   = self.FramePlotParams(self)
        self.frm_plt     = self.FramePlot(self)
        self.frm_process = self.FrameProcess(self)
        self.frm_output  = self.FrameOutput(self)


        # Frames gridding
        self.menubar.grid(row=0, column=0, sticky='nw', columnspan=2)
        self.frm_waves.grid(row=1, column=0, sticky='nw')
        self.frm_plt_p.grid(row=2, column=0, sticky='nw')
        self.frm_plt.grid(row=1, column=1, rowspan=self.grid_size()[1]+2)
        self.frm_process.grid(row=3, column=0, sticky='nw')
        self.frm_output.grid(row=4, column=0, sticky='nw')

        # Shortcut-keys
        self.bind('<r>', self.process)
        self.bind('<f>', self.select_next_trace)

    class FrameMenu(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent

            self.settings_mb = tk.Menubutton(self, text='Settings')
            # self.settings_mb.grid(row=0, column=0)

            self.settings_mn = tk.Menu(self.settings_mb, tearoff=0)
            self.settings_mb['menu'] = self.settings_mn

            self.settings_mn.add_command(
                label='Connections',
                command=lambda: parent.open_window(parent.WindowSettings(parent))
            )
            self.settings_mn.add_command(label='Spectrogram')#, command=donothing)

            self.plot_results_btn = tk.Button(
                self,
                text='Plot database results',
                command=lambda: parent.open_window(parent.WindowPlotResults(parent))
            )
            self.plot_results_btn.grid(row=0, column=0)

            self.spec_cfg_btn = tk.Button(
                self,
                text='Spectrogram settings',
                command=lambda: self.master.open_window(
                    self.master.WindowSpecSettings(parent)
                )
            )
            self.spec_cfg_btn.grid(row=0, column=1)

            self.overwrite_c_btn = tk.Button(
                self,
                text='Overwrite configuration',
                command=self.master.overwrite_c
            )
            self.overwrite_c_btn.grid(row=0, column=2)

            self.quit_btn = tk.Button(
                self,
                text='Quit',
                command=self.parent.destroy
            )
            self.quit_btn.grid(row=0, column=3)

    class FrameWaves(tk.LabelFrame):
        def __init__(self, parent):
            super().__init__(
                parent,
                text='1. Waveforms',
                font=parent.font_title,
                bd=parent.bd,
                relief=parent.relief,
            )
            width = 17

            self.parent = parent

            # Volcano
            self.volcano_lbl = tk.Label(self, text='Volcano')
            self.get_volcanoes(parent.conn)

            # Station
            self.stacha_lf = tk.LabelFrame(self, text='Station/channel')

            self.station_lbl = tk.Label(self, text='Station(s)')
            self.station_lbx = tk.Listbox(self.stacha_lf, selectmode=tk.MULTIPLE,
                                          height=3, width=7)
            self.station_sb = tk.Scrollbar(self.stacha_lf)
            self.station_lbx.config(yscrollcommand=self.station_sb.set,
                                    exportselection=False)
            self.station_sb.config(command=self.station_lbx.yview)

            # Channel
            self.channel_lbl = tk.Label(self, text='Channel(s)')

            self.channel_lbx = tk.Listbox(self.stacha_lf, selectmode=tk.MULTIPLE,
                                          height=3, width=7)
            self.channel_lbx.config(exportselection=False)

            for channel in ['HHE', 'HHN', 'HHZ', 'HDF']:
                self.channel_lbx.insert(tk.END, channel)

            # Swarm file for datetimes
            self.swarm_lf = tk.LabelFrame(self, text='CSV file')
            self.swarm_check_iv = tk.IntVar(self, value=1)
            self.swarm_cb = tk.Checkbutton(
                self.swarm_lf,
                variable=self.swarm_check_iv,
                command=self.switch
            )

            self.swarm_btn = tk.Button(
                self.swarm_lf,
                text='Select file',
                command=self.select_file
            )
            # self.swarm_btn.config(state='disabled')

            self.swarm_lbx = tk.Listbox(self.swarm_lf, height=3, width=width)
            self.swarm_sb = tk.Scrollbar(self.swarm_lf)
            self.swarm_lbx.config(yscrollcommand=self.swarm_sb.set,
                                    exportselection=False)
            self.swarm_sb.config(command=self.swarm_lbx.yview)

            self.starttime_lbl = tk.Label(self, text='Start time')
            self.starttime_ent = tk.Entry(self, width=width)
            self.starttime_ent.insert(
                tk.END,
                (datetime.today()-timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            )
            self.starttime_ent.config(state='disabled')

            self.duration_lbl = tk.Label(self, text='Duration [s]')
            self.duration_ent = tk.Entry(self, width=width)
            self.duration_ent.insert(tk.END, self.master.c.duration)

            self.download_btn = tk.Button(
                self,
                text='Download',
                command=parent.download
            )

            self.volcano_lbl.grid(row=0)
            self.volcano_om.grid(row=1, column=0)
            self.stacha_lf.grid(row=2)
            self.swarm_lf.grid(row=6)
            self.starttime_lbl.grid(row=7)
            self.starttime_ent.grid(row=8)
            self.duration_lbl.grid(row=9)
            self.duration_ent.grid(row=10)
            self.download_btn.grid(row=11)

            self.station_lbx.grid(row=0)
            self.station_sb.grid(row=0, column=1)
            self.channel_lbx.grid(row=0, column=2)

            self.swarm_cb.grid(row=0)
            self.swarm_btn.grid(row=0, column=1)
            self.swarm_lbx.grid(row=1, column=0, columnspan=2)
            self.swarm_sb.grid(row=1, column=2)

        def get_volcanoes(self, conn):
            df = pd.read_sql_query('SELECT volcano FROM volcano;', conn)
            volcanoes = df.volcano.tolist()

            self.volcanoes_sv = tk.StringVar(self)
            self.volcano_om = tk.OptionMenu(
                self,
                self.volcanoes_sv,
                *(volcanoes),
                command=self.get_stations,
            )
            return

        def get_stations(self, event):
            volcano = self.volcanoes_sv.get()

            df = pd.read_sql_query(
                f"""
                SELECT station FROM station
                WHERE volcano = '{volcano}'
                """,
                self.parent.conn
            )
            stations = sorted(df.station.tolist())

            self.station_lbx.delete(0, tk.END)
            for station in stations:
                self.station_lbx.insert(tk.END, station)

        def switch(self):
            if self.swarm_btn['state'] == 'normal':
                self.swarm_btn['state'] = 'disabled'
                self.swarm_lbx['state'] = 'disabled'
                self.starttime_ent['state'] = 'normal'
            else:
                self.swarm_btn['state'] = 'normal'
                self.swarm_lbx['state'] = 'normal'
                self.starttime_ent['state'] = 'disabled'

        def select_file(self):
            filetypes = (
                ('Comma separated values', '*.csv'),
                ('All files', '*.*')
            )

            self.swarm_file = tk.filedialog.askopenfilename(
                title='Open Swarm labels file',
                initialdir=self.parent.c.swarm_dir,
                filetypes=filetypes
            )

            df = pd.read_csv(self.swarm_file, usecols=[0], names=['datetime'])
            self.swarm_lbx.delete(0, tk.END)
            for i, row in df.iterrows():
                self.swarm_lbx.insert(tk.END, row.datetime)

    class FramePlotParams(tk.LabelFrame):
        def __init__(self, parent):
            super().__init__(
                parent,
                text='2. Select trace (next: f)',
                font=parent.font_title,
                bd=parent.bd,
                relief=parent.relief,
            )

            self.stacha_lbx = tk.Listbox(self, height=3, exportselection=False)
            self.stacha_lbx.bind('<<ListboxSelect>>', self.master.select_trace)
            self.stacha_lbx.grid()

    class FramePlot(tk.LabelFrame):
        def __init__(self, parent):
            text = '3. Picking with right-click button (3 times)'
            super().__init__(
                parent,
                text=text,
                font=parent.font_title,
                bd=parent.bd,
                relief=parent.relief,
            )

    class FrameProcess(tk.LabelFrame):
        def __init__(self, parent):
            super().__init__(
                parent,
                text='4. Process',
                font=parent.font_title,
                bd=parent.bd,
                relief=parent.relief,
            )
            validatefloat = self.register(self.master.isfloat)

            width = 4

            self.filter_lf= tk.LabelFrame(
                self,
                text='Butterworth bandpass filter',
            )

            self.freqmin_lbl = tk.Label(self.filter_lf, text='min(f) [Hz]')
            self.freqmin_svr = tk.DoubleVar(self)
            self.freqmin_svr.set(self.master.c.process.freqmin)
            self.freqmin_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'freqmin', self.freqmin_svr
                )
            )


            self.freqmin_ent = tk.Entry(
                self.filter_lf, textvariable=self.freqmin_svr, width=width,
                validate='all', validatecommand=(validatefloat, '%P'),
            )

            self.freqmax_lbl = tk.Label(self.filter_lf, text='max(f) [Hz]')
            self.freqmax_svr = tk.DoubleVar(self)
            self.freqmax_svr.set(self.master.c.process.freqmax)

            self.freqmax_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'freqmax', self.freqmax_svr
                )
            )
            self.freqmax_ent = tk.Entry(
                self.filter_lf, textvariable=self.freqmax_svr, width=width,
                validate='all', validatecommand=(validatefloat, '%P'),
            )

            self.order_lbl = tk.Label(self.filter_lf, text='Order')
            self.order_svr = tk.IntVar(self)
            self.order_svr.set(self.master.c.process.order)
            self.order_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'order', self.order_svr
                )
            )
            self.order_ent = tk.Entry(
                self.filter_lf, textvariable=self.order_svr, width=width,
                validate='all', validatecommand=(validatefloat, '%P'),
            )

            self.factor_lbl = tk.Label(self, text='Threshold multiplier')
            self.factor_svr = tk.IntVar(self)
            self.factor_svr.set(self.master.c.process.factor)
            self.factor_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'factor', self.factor_svr
                )
            )
            self.factor_ent = tk.Entry(
                self, textvariable=self.factor_svr, width=width,
                validate='all', validatecommand=(validatefloat, '%P'),
            )

            self.distance_Hz_lbl = tk.Label(self, text='Minimum distance [Hz]')
            self.distance_Hz_svr = tk.DoubleVar(self)
            self.distance_Hz_svr.set(self.master.c.process.distance_Hz)
            self.distance_Hz_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'distance_Hz', self.distance_Hz_svr
                )
            )
            self.distance_Hz_ent = tk.Entry(
                self, textvariable=self.distance_Hz_svr, width=width,
                validate='all', validatecommand=(validatefloat, '%P'),
            )

            self.process_btn = tk.Button(
                self,
                text='Extract spectral peaks (r)',
                command=lambda: parent.process('')
            )

            self.filter_lf.grid(row=0, column=0, columnspan=2)
            self.factor_lbl.grid(row=1, column=0)
            self.factor_ent.grid(row=1, column=1)
            self.distance_Hz_lbl.grid(row=2, column=0)
            self.distance_Hz_ent.grid(row=2, column=1)
            self.process_btn.grid(row=3, column=0, columnspan=2)

            self.freqmin_lbl.grid(row=0, column=0)
            self.freqmax_lbl.grid(row=0, column=1)
            self.order_lbl.grid(row=0, column=2)
            self.freqmin_ent.grid(row=1, column=0)
            self.freqmax_ent.grid(row=1, column=1)
            self.order_ent.grid(row=1, column=2)

        def set_conf_change(self, var, indx, mode, key, tkvar):
            try:
                self.master.c.process.__setitem__(key, tkvar.get())
            except:
                pass

    class FrameOutput(tk.LabelFrame):
        def __init__(self, parent):
            super().__init__(
                parent,
                text='5. Output',
                font=parent.font_title,
                bd=parent.bd,
                relief=parent.relief,
            )

            self.results_btn = tk.Button(
                self,
                text='View results & submit',
                command=lambda: parent.open_window(parent.WindowResults(parent))
            )
            self.results_btn.pack()

    class WindowSettings(tk.Toplevel):
        def __init__(self, parent):
            super().__init__(parent)
            self.title('Connections settings')

            self.cfg_file_msg = tk.Message(
                self,
                text=(
                    'Default values for these settings are read from your '
                    '~/.tonusrc file. Connection is made automatically at '
                    'start-up. You can modify them here and re-connect.'
                )
            )

            self.ip_lbl = tk.Label(self, text='FDSN IP address')
            self.ip_ent = tk.Entry(self)
            self.ip_ent.insert(tk.END, self.master.c.fdsn.ip)

            self.port_lbl = tk.Label(self, text='FDSN port')
            self.port_ent = tk.Entry(self)
            self.port_ent.insert(tk.END, self.master.c.fdsn.port)

            self.conn_btn = tk.Button(
                self,
                text='Connect',
                command=lambda: parent.connect_waveserver(
                    self.ip_ent.get(),
                    self.port_ent.get(),
                )
            )
            self.ok_btn = tk.Button(self, text='OK', command=self._destroy)

            widgets = [
                self.cfg_file_msg,
                self.ip_lbl,
                self.ip_ent,
                self.port_lbl,
                self.port_ent,
                self.conn_btn,
                self.ok_btn,
            ]
            for row, widget in enumerate(widgets):
                widget.grid(row=row, column=0)

        def _destroy(self):
            self.master.focus_force()
            self.destroy()

    class WindowSpecSettings(tk.Toplevel):
        def __init__(self, parent):
            super().__init__(parent)
            self.title('Spectrogram settings')

            quit_btn = tk.Button(self, text='Close', command=self._destroy)

            self.window_lf = tk.LabelFrame(self, text='Window')
            self.yaxis_lf  = tk.LabelFrame(self, text='Y-axis')
            self.cmap_lf   = tk.LabelFrame(self, text='Color map')

            self.window_lf.grid(row=0, column=0)
            self.yaxis_lf.grid(row=1, column=0)
            self.cmap_lf.grid(row=2, column=0)
            quit_btn.grid(row=3, column=0)

            ###################################################################

            nfft = [2**n for n in range(6, 12)]
            self.nfft_lb = tk.Label(self.window_lf, text='Window length [samples]')
            self.nfft_sv = tk.IntVar(self)
            self.nfft_sv.set(self.master.c.spectrogram.nfft)
            self.nfft_om = tk.OptionMenu(
                self.window_lf,
                self.nfft_sv,
                *(nfft),
                command=self.set_nfft
            )

            self.mult_lbl = tk.Label(self.window_lf, text='Resolution multplier')
            self.mult_svr = tk.IntVar(self)
            self.mult_svr.set(self.master.c.spectrogram.mult)
            self.mult_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'mult', self.mult_svr.get()
                )
            )
            self.mult_ent = tk.Entry(self.window_lf, textvariable=self.mult_svr)

            self.per_lap_lbl = tk.Label(self.window_lf, text='Overlap [%]')
            self.per_lap_svr = tk.DoubleVar(self)
            self.per_lap_svr.set(self.master.c.spectrogram.per_lap)
            self.per_lap_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'per_lap', self.per_lap_svr.get()
                )
            )
            self.per_lap_ent = tk.Entry(self.window_lf, textvariable=self.per_lap_svr)

            self.nfft_lb.grid(row=0, column=0)
            self.nfft_om.grid(row=1, column=0)
            self.mult_lbl.grid(row=2, column=0)
            self.mult_ent.grid(row=3, column=0)
            self.per_lap_lbl.grid(row=4, column=0)
            self.per_lap_ent.grid(row=5, column=0)

            ###################################################################

            self.ymin_lbl = tk.Label(self.yaxis_lf, text='min(f) [Hz]')
            self.ymin_svr = tk.DoubleVar(self)
            self.ymin_svr.set(self.master.c.spectrogram.ymin)
            self.ymin_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'ymin', self.ymin_svr.get()
                )
            )
            self.ymin_ent = tk.Entry(self.yaxis_lf, textvariable=self.ymin_svr,
                                    width=4)

            self.ymax_lbl = tk.Label(self.yaxis_lf, text='min(f) [Hz]')
            self.ymax_svr = tk.DoubleVar(self)
            self.ymax_svr.set(self.master.c.spectrogram.ymax)
            self.ymax_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'ymax', self.ymax_svr.get()
                )
            )
            self.ymax_ent = tk.Entry(self.yaxis_lf, textvariable=self.ymax_svr,
                                    width=4)

            self.ymin_lbl.grid(row=0, column=0)
            self.ymin_ent.grid(row=1, column=0)
            self.ymax_lbl.grid(row=0, column=1)
            self.ymax_ent.grid(row=1, column=1)

            ###################################################################

            self.cmap_lbl = tk.Label(self.cmap_lf, text='Colormap')
            self.cmap_svr = tk.StringVar(self)
            self.cmap_svr.set(self.master.c.spectrogram.cmap)
            self.cmap_om = tk.OptionMenu(
                self.cmap_lf,
                self.cmap_svr,
                *(plt.colormaps()),
                command=self.set_cmap
            )

            self.std_factor_lbl = tk.Label(self.cmap_lf, text='STD multiplier')
            self.std_factor_svr = tk.IntVar(self)
            self.std_factor_svr.set(self.master.c.spectrogram.std_factor)
            self.std_factor_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'std_factor', self.std_factor_svr.get()
                )
            )
            self.std_factor_ent = tk.Entry(self.cmap_lf,
                                           textvariable=self.std_factor_svr)

            self.cmap_lbl.grid(row=0, column=0)
            self.cmap_om.grid(row=1, column=0)
            self.std_factor_lbl.grid(row=2, column=0)
            self.std_factor_ent.grid(row=3, column=0)

            ###################################################################


        def set_nfft(self, event):
            self.master.c.spectrogram.nfft = self.nfft_sv.get()

        def set_cmap(self, event):
            self.master.c.spectrogram.cmap = self.cmap_svr.get()

        def set_conf_change(self, var, indx, mode, key, value):
            self.master.c.spectrogram.__setitem__(key, value)

        def _destroy(self):
            self.master.focus_force()
            self.destroy()

    class WindowResults(tk.Toplevel):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            self.title('Output')

            self.quit_btn = tk.Button(self, text='Close', command=self._destroy)

            self.peaks_lf = tk.LabelFrame(self, text='Peaks detected')

            self.channels_lbl = tk.Label(self, text='Channels processed')
            self.channels_lbx = tk.Listbox(self, height=3)
            self.channels_lbx.delete(0, tk.END)
            self.channels_lbx.bind("<<ListboxSelect>>", self.create_table)
            try:
                for stacha in parent.results:
                    if 'peaks' in parent.results[stacha].keys():
                        self.channels_lbx.insert(tk.END, stacha)
                self.channels_lbx.select_set(0)
                self.channels_lbx.event_generate('<<ListboxSelect>>')
                self.channels_lbx.focus_set()
            except:
                pass

            self.submit_btn = tk.Button(
                self,
                text='Submit',
                command=self.submit
            )

            self.quit_btn.grid(row=0)
            self.channels_lbl.grid(row=1)
            self.channels_lbx.grid(row=2)
            self.peaks_lf.grid(row=3)
            self.submit_btn.grid(row=4)
            header = ['Frequency [Hz]', 'Amplitude [um/s]', 'Q_f']

            table = Table(self.peaks_lf, header, [])

        def _destroy(self):
            self.master.focus_force()
            self.destroy()

        def create_table(self, event):
            selection = self.channels_lbx.curselection()
            if len(selection) < 1:
                return
            stacha = self.channels_lbx.get(selection[0])

            header = ['Frequency [Hz]', 'Amplitude [um/s]', 'Q_f']

            frequency = [
                round(f, 2) for f in
                self.parent.results[stacha]['peaks']['frequency']
            ]

            amplitude = [
                round(a, 2) for a in
                self.parent.results[stacha]['peaks']['amplitude']
            ]

            q_f = [
                round(q, 0) for q in
                self.parent.results[stacha]['peaks']['q_f']
            ]
            columns = [frequency, amplitude, q_f]

            for widget in self.peaks_lf.winfo_children():
                widget.destroy()

            table = Table(self.peaks_lf, header, columns)

        def submit(self):
            submitted = False

            cur = self.master.conn.cursor()

            # Clean channels not picked
            results = {}
            for stacha in self.master.results.keys():
                if self.master.results[stacha] != {}:
                    results[stacha] = self.master.results[stacha]
            self.master.results = results

            if self.master.event_id is None:
                volcano = self.master.frm_waves.volcanoes_sv.get()
                cur.execute(f"SELECT id FROM volcano WHERE volcano = '{volcano}';")
                volcano_id = cur.fetchone()[0]

                starttimes, endtimes = [], []
                for stacha in self.master.results.keys():
                    starttimes.append(UTCDateTime(self.master.results[stacha]['t1']))
                    endtimes.append(UTCDateTime(self.master.results[stacha]['t3']))
                starttime = min(starttimes).datetime
                endtime   = max(endtimes).datetime

                sql_str = f"""
                INSERT INTO event(starttime, endtime, volcano_id)
                VALUES('{starttime}', '{endtime}', {volcano_id})
                RETURNING id
                """
                cur.execute(sql_str)
                self.master.event_id = cur.fetchone()[0]

            for stacha in self.master.results.keys():
                station, channel = stacha.split()
                cur.execute(
                   f"""
                    SELECT id FROM channel
                    WHERE channel = '{channel}'
                    AND station = '{station}';
                    """
                )
                channel_id = cur.fetchone()[0]

                t1 = UTCDateTime(self.master.results[stacha]['t1']).datetime
                t2 = UTCDateTime(self.master.results[stacha]['t2']).datetime
                t3 = UTCDateTime(self.master.results[stacha]['t3']).datetime
                q_alpha = self.master.results[stacha]['q_alpha']

                sql_str = f"""
                INSERT INTO
                    tornillo(channel_id, t1, t2, t3, event_id, q_alpha)
                VALUES(
                    {channel_id}, '{t1}', '{t2}', '{t3}',
                    {self.master.event_id}, {q_alpha}
                )
                RETURNING
                    id
                """
                try:
                    cur.execute(sql_str)
                    tornillo_id = cur.fetchone()[0]

                    frequency = self.master.results[stacha]['peaks']['frequency']
                    amplitude = self.master.results[stacha]['peaks']['amplitude']
                    q_f       = self.master.results[stacha]['peaks']['q_f']

                    for f, a, q in zip(frequency, amplitude, q_f):
                        cur.execute(
                            f"""
                            INSERT INTO
                                tornillo_peaks(tornillo_id, frequency,
                                amplitude, q_f)
                            VALUES(
                                {tornillo_id}, {round(f, 3)},
                                {a}, {round(q, 2)})
                            """
                        )
                    submitted = True
                except Exception as e:
                    tk.messagebox.showerror('Data already submitted', e)
                    self.master.conn.commit()

            self.master.conn.commit()
            if submitted:
                tk.messagebox.showinfo('Submission succesful',
                                       'Data has been written to the database')
                self._destroy()

    class WindowPlotResults(tk.Toplevel):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            self.conn = parent.conn
            self.title('Plot database results')

            self.quit_btn = tk.Button(self, text='Close', command=self._destroy)
            self.selec_frm = self.FrameSelection(self, parent.conn)

            self.plot_selec_frm = self.FramePlotSelection(self, parent.conn)

            self.plot_db_lf = tk.LabelFrame(self, text='Plot')

            self.download_csv_btn = tk.Button(
                self,
                text='Download CSV',
                command=self.download_csv
            )

            self.quit_btn.grid(row=0, column=0)
            self.selec_frm.grid(row=1, column=0)
            self.download_csv_btn.grid(row=2, column=0)
            self.plot_selec_frm.grid(row=3, column=0)
            self.plot_db_lf.grid(row=0, column=1, rowspan=self.grid_size()[1]+1)

        class FrameSelection(tk.LabelFrame):
            def __init__(self, parent, conn):
                super().__init__(parent, text='1. Data Selection')
                self.conn = conn

                self.volcano_lbl = tk.Label(self, text='Volcano')
                self.volcano_lbl.pack()

                query = f"""
                SELECT volcano FROM volcano
                WHERE EXISTS
                (SELECT 1 FROM event
                WHERE event.volcano_id = volcano.id LIMIT 1);
                """
                df = pd.read_sql_query(query, conn)

                volcanoes = df.volcano.tolist()

                self.volcanoes_sv = tk.StringVar(self)
                self.volcano_om = tk.OptionMenu(
                    self,
                    self.volcanoes_sv,
                    *(volcanoes),
                    command=self.get_stacha
                )
                self.volcano_om.pack()

                self.stacha_lbl = tk.Label(self, text='Channel(s)')
                self.stacha_lbl.pack()
                self.stacha_lbx = tk.Listbox(self, selectmode=tk.MULTIPLE,
                                             height=3)
                self.stacha_lbx.pack()
                self.download_db_btn = tk.Button(
                    self,
                    text='Download',
                    command=self.download_db
                )
                self.download_db_btn.pack()


            def get_stacha(self, event):
                volcano = self.volcanoes_sv.get()

                query = f"""
                SELECT channel.station, channel.channel, channel.id
                FROM channel
                INNER JOIN station ON channel.station_id = station.id
                INNER JOIN volcano ON station.volcano_id = volcano.id
                WHERE volcano.volcano = '{volcano}'
                AND EXISTS
                (SELECT 1 FROM tornillo
                WHERE tornillo.channel_id = channel.id LIMIT 1)
                """

                df = pd.read_sql_query(query, self.conn)

                self.stacha_lbx.delete(0, tk.END)
                for i, row in df.iterrows():
                    self.stacha_lbx.insert(
                        tk.END, f'{row.station} {row.channel} {row.id}')

            def download_db(self):
                selection = self.stacha_lbx.curselection()
                stachas = [self.stacha_lbx.get(s) for s in selection]
                channel_ids = [stacha.split()[2] for stacha in stachas]

                query = f"""
                SELECT
                    tornillo.t1, tornillo.t2, tornillo.t3,
                    tornillo.channel_id, tornillo.event_id,
                    tornillo_peaks.frequency, tornillo_peaks.q_f,
                    tornillo_peaks.amplitude,
                    channel.station, channel.channel
                FROM
                    tornillo_peaks
                INNER JOIN
                    tornillo ON tornillo_peaks.tornillo_id = tornillo.id
                INNER JOIN
                    channel ON tornillo.channel_id = channel.id
                WHERE
                    tornillo.channel_id IN ({','.join(channel_ids)});
                """

                df = pd.read_sql_query(query, self.conn)

                df['stacha'] = df.station + ' ' + df.channel + ' ' +\
                        df.channel_id.apply(str)

                for t in 't1 t2 t3'.split():
                    df[t] = df[t].dt.tz_convert('America/Guatemala')

                self.master.df = df

                self.master.plot_selec_frm.stacha_lbx.delete(0, tk.END)
                for stacha in df.stacha.unique():
                    self.master.plot_selec_frm.stacha_lbx.insert(tk.END, stacha)

                query = f"""
                SELECT
                    event.starttime, event.id, tornillo.channel_id
                FROM
                    event
                INNER JOIN
                    tornillo ON tornillo.event_id = event.id
                INNER JOIN
                    channel ON tornillo.channel_id = channel.id
                WHERE
                    tornillo.channel_id IN ({','.join(channel_ids)});
                """
                df = pd.read_sql_query(query, self.conn)

                self.master.hist = df

        class FramePlotSelection(tk.LabelFrame):
            def __init__(self, parent, conn):
                super().__init__(parent, text='2. Plotting')
                self.conn = conn

                self.stacha_lbl = tk.Label(self, text='Channel(s)')
                self.stacha_lbl.pack()
                self.stacha_lbx = tk.Listbox(self, selectmode=tk.MULTIPLE,
                                             height=3)
                self.stacha_lbx.pack()

                self.plot_btn = tk.Button(
                    self,
                    text='Plot',
                    command=self.plot
                )
                self.plot_btn.pack()

            def plot(self):
                selection = self.stacha_lbx.curselection()
                stachas = [self.stacha_lbx.get(s) for s in selection]
                channel_ids = [int(stacha.split()[2]) for stacha in stachas]

                df = self.master.df
                df = df[df.channel_id.isin(channel_ids)]

                hist = self.master.hist
                hist = hist[hist.channel_id.isin(channel_ids)]
                hist = hist.groupby('id').min()
                hist.index = hist.starttime.dt.tz_convert('America/Guatemala')
                hist = hist.drop(hist.columns[:-1], axis=1)
                hist.columns = ['n']
                hist = hist.resample('D').count()

                self.fig = plt.figure(figsize=(6, 6.5))
                self.fig.subplots_adjust(left=.1, bottom=.07, right=.9, top=.98,
                                    wspace=.2, hspace=.15)
                try:
                    ax1.remove()
                except:
                    pass

                rows = 4
                cols = 1

                ax1 = self.fig.add_subplot(rows, cols, 1)
                ax1.set_ylabel('Frequency [Hz]')

                ax2 = self.fig.add_subplot(rows, cols, 2, sharex=ax1)
                ax2.set_ylabel('Q')

                ax3 = self.fig.add_subplot(rows, cols, 3, sharex=ax1)
                ax3.set_ylabel('Amplitude [$\mu m/s$]')

                ax4 = self.fig.add_subplot(rows, cols, 4, sharex=ax1)
                ax4.set_ylabel('Number of daily events')

                smin, smax = 20, 50
                alpha = 0.5

                df = df[~df.isin([np.nan, np.inf, -np.inf]).any(1)]


                for stacha in stachas:
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
                    ax3.scatter(a.t1, a.amplitude, label=stacha, lw=0.5,
                               edgecolor='grey', s=20)
                    ax3.set_yscale('log')

                ax4.bar(hist.index, hist.n, edgecolor='gray', linewidth=0.3)

                for ax in self.fig.get_axes():
                    ax.grid('on', alpha=alpha)
                ax2.legend()
                self.canvas = FigureCanvasTkAgg(self.fig,
                                                master=self.master.plot_db_lf)
                self.canvas.draw()
                self.canvas.get_tk_widget().grid(row=0, column=0)

                self.toolbarFrame = tk.Frame(master=self.master.plot_db_lf)
                self.toolbarFrame.grid(row=1, column=0)
                self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbarFrame)

        def _destroy(self):
            self.master.focus_force()
            self.destroy()

        def download_csv(self):
            filetypes = (
                ('Comma separated values', '*.csv'),
                ('All files', '*.*')
            )
            outpath = tk.filedialog.asksaveasfile(
                title='Open output file',
                filetypes=filetypes
            )
            if outpath is None:
                return
            self.df.to_csv(outpath, index=False)
            pass

    def _set_conf(self):
        try:
            self.c = set_conf()
        except Exception as e:
            logging.error(e)
            text = (
                f'Configuration {CONF_FILEPATH} file missing. '
                'Copy it from tonus/ and modify it.'
            )
            tk.messagebox.showwarning('Configuration file missing', text)
            self.destroy()

    def isfloat(self, what):
        if what == '':
            return True
        try:
            float(what)
            return True
        except ValueError:
            return False

    def isntfloat(self, widget, value):
        widget.set(value)

    def open_window(self, window):
        window.transient(self)
        window.grab_set()
        self.wait_window(window)

    def connect_waveserver(self, ip, port):
        url = f'http://{ip}:{port}'
        try:
            logging.info(f'Connecting to {url}...')
            self.client = Client(url)
            logging.info('Succesfully connected to FDSN client.')
            return self.client
        except Exception as e:
            print(e)

    def check_event(self):
        pre_pick = 20
        volcano = self.frm_waves.volcanoes_sv.get()

        if self.frm_waves.starttime_ent['state'] == 'disabled':
            selection = self.frm_waves.swarm_lbx.curselection()
            self.starttime = UTCDateTime(
                self.frm_waves.swarm_lbx.get(selection[0])
            ) - pre_pick
        else:
            self.starttime = UTCDateTime(self.frm_waves.starttime_ent.get())
        duration = float(self.frm_waves.duration_ent.get())
        self.endtime = self.starttime + duration

        query = f"""
        SELECT event.* FROM event
        INNER JOIN volcano ON event.volcano_id = volcano.id
        AND volcano.volcano = '{volcano}'
        AND (starttime BETWEEN timestamp '{self.starttime.datetime}'
        and timestamp '{self.endtime.datetime}');
        """

        df = pd.read_sql_query(query, self.conn)

        if len(df) > 0:
            self.event_id = df.id.to_list()[0]

            df = pd.read_sql_query(
                f"""
                SELECT * FROM tornillo
                WHERE event_id = {self.event_id} ;
                """,
                self.conn
            )
            if len(df) > 0:
                channel_ids = ', '.join(str(c) for c in df.channel_id.tolist())

                query = f"""
                SELECT station, channel FROM channel
                WHERE id IN ({channel_ids})
                """
                df = pd.read_sql_query(query, self.conn)
                stachas = ', '.join(
                    [f'{row.station} {row.channel}' for i, row in df.iterrows()]
                )

                text=(
                    'There is already an analysed event '
                    f'(ID = {self.event_id}), '
                    f'in the time range requested '
                    f'in stations/channels: {stachas}. '
                    f'Do not process this channels, else any new results from '
                    'other channels will not be submitted. '
                )
                tk.messagebox.showwarning('Event already analysed', text)
            else:
                text=(
                    f'There is already an event (ID = {self.event_id}) in the database '
                    'in the time range requested, but not analysed yet. '
                    'Any further results will be associated to this event.'
                )
                tk.messagebox.showwarning('Event in database', text)
        else:
            self.event_id = None

    def download(self):
        self.check_event()
        logging.info('Downloading waveforms...')

        selection = self.frm_waves.station_lbx.curselection()
        station = ','.join(
            [self.frm_waves.station_lbx.get(s) for s in selection]
        )

        selection = self.frm_waves.channel_lbx.curselection()
        channel = ','.join(
            [self.frm_waves.channel_lbx.get(s) for s in selection]
        )

        self.st = self.client.get_waveforms(
            self.c.network, station, '*', channel,
            self.starttime, self.endtime, attach_response=True
        )
        self.pre_process()
        logging.info('Stream downloaded.')

        self.st.sort(keys=['station'])
        # Change station/channel options for plotting
        stachas = [
            f'{tr.stats.station} {tr.stats.channel}' for tr in self.st
        ]
        # Initialize the results holder:
        self.results = {}

        self.frm_plt_p.stacha_lbx.delete(0, tk.END)
        for stacha in stachas:
            self.frm_plt_p.stacha_lbx.insert(tk.END, stacha)
        self.frm_plt_p.stacha_lbx.select_set(0)
        self.frm_plt_p.stacha_lbx.event_generate("<<ListboxSelect>>")

        for stacha in stachas:
            self.results[stacha] = {}

    def pre_process(self):
        self.st.detrend()
        self.st.remove_response()
        self.st.filter('highpass', freq=0.5)

    def select_trace(self, event):
        # station, channel = tuple(self.frm_plt_p.stacha_sv.get().split())
        selection = self.frm_plt_p.stacha_lbx.curselection()
        if len(selection) < 1:
            return
        stacha = self.frm_plt_p.stacha_lbx.get(selection[0])
        station, channel = stacha.split()
        self.tr = self.st.select(station=station, channel=channel)[0]
        plt.close()
        self.plot()

    def select_next_trace(self, event):
        selected_trace = self.frm_plt_p.stacha_lbx.curselection()[0]
        n_traces = self.frm_plt_p.stacha_lbx.size()

        if selected_trace < n_traces-1:
            self.frm_plt_p.stacha_lbx.selection_clear(0, tk.END)
            self.frm_plt_p.stacha_lbx.select_set(selected_trace+1)
            self.frm_plt_p.stacha_lbx.event_generate('<<ListboxSelect>>')
        else:
            self.open_window(self.WindowResults(self))

    def spectrogram(self,
        tr, ax,
        dbscale=True,
        get_v=True,
    ):
        nfft       = self.c.spectrogram.nfft
        mult       = self.c.spectrogram.mult
        per_lap    = self.c.spectrogram.per_lap
        ylim       = (self.c.spectrogram.ymin, self.c.spectrogram.ymax)
        cmap       = self.c.spectrogram.cmap
        std_factor = self.c.spectrogram.std_factor

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
            specgram = ax.pcolormesh(t, f, np.log(Sxx), cmap=cmap, vmin=vmin,
                                      vmax=vmax)
        else:
            specgram = ax.pcolormesh(t, f, (Sxx), cmap=cmap, vmin=vmin, vmax=vmax)

        ax.set_ylim(ylim)
        return

    def plot(self):
        tr = self.tr
        stacha = f'{tr.stats.station} {tr.stats.channel}'

        time_str = str(tr.stats.starttime)[:-8].replace('T',' ')

        time = np.arange(0, tr.stats.npts/tr.stats.sampling_rate, tr.stats.delta)
        if len(time) > len(tr.data):
            time = time[:-1]

        self.fig = plt.figure(figsize=(8, 6))

        self.fig.subplots_adjust(left=.07, bottom=.07, right=.94, top=0.962,
                            wspace=.04, hspace=.12)

        gs = gridspec.GridSpec(nrows=2, ncols=2, width_ratios=[2, 1],
                               height_ratios=[1, 3])

        _ax1 = self.fig.add_subplot(gs[0, 0])

        ax1 = self.fig.add_subplot(gs[0, 0], zorder=2)
        ax1.plot(time, tr.data, linewidth=0.7)
        ax1.set_xlim(time.min(), time.max())
        # ax1.ticklabel_format(axis='y', style='sci', scilimits=(0, 0),
        #                      useMathText=True)

        ax1.axis("off")

        # Re-scale with zoom
        _ax1.set_navigate(False)
        _ax1.set_xlim(ax1.get_xlim())
        _ax1.set_ylim(ax1.get_ylim())
        _ax1.set_ylabel('Amplitude [m/s]')

        ax2 = self.fig.add_subplot(gs[1, 0], sharex=ax1)
        self.spectrogram(tr, ax2)
        ax2.set_ylabel('Frequency [Hz]')
        ax2.set_xlabel('Time [s]')


        def on_lims_change(axes):
            try:
                xmin, xmax = ax1.get_xlim()
                _ax1.set_xlim(xmin, xmax)
                y = tr.data[np.where((time >= xmin) & (time <= xmax))]

                margin = (y.max() - y.min()) * 0.05
                _ax1.set_ylim(y.min()-margin, y.max()+margin)
                ax1.set_ylim(y.min()-margin, y.max()+margin)
            except:
                return
        ax1.callbacks.connect('xlim_changed', on_lims_change)
        ax1.callbacks.connect('ylim_changed', on_lims_change)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plt)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0)

        self.toolbarFrame = tk.Frame(master=self.frm_plt)
        self.toolbarFrame.grid(row=1, column=0)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbarFrame)
        self.toolbar.focus_force()

        self.canvas.mpl_connect('key_press_event', key_press_handler)

        self.count = 0

        for t in ['t1', 't2', 't3']:
            if stacha in self.results.keys():
                if t in self.results[stacha].keys():
                    self.count += 1
                    for ax in self.fig.get_axes()[1:3]:
                        xdata = UTCDateTime(
                            self.results[stacha][t]
                        ) - tr.stats.starttime
                        ax.axvline(x=xdata, linewidth=1, c='r', ls='--')

        # if self.count == 3:
        #     self.process('')

        def _pick(event):
            if event.button == 3:
                if self.count < 3:
                    for ax in self.fig.get_axes()[1:3]:
                        ax.axvline(x=event.xdata, linewidth=1, c='r', ls='--')
                        self.canvas.draw()
                    t = tr.stats.starttime + event.xdata
                    logging.info(f'Time picked: {t}')
                    self.results[stacha][f't{self.count+1}'] = str(t)
                self.count += 1
                if self.count == 3:
                    self.process('')
        self.fig.canvas.mpl_connect('button_press_event', _pick)

        self.multi = MultiCursor(self.fig.canvas, (ax1, ax2), color='r', lw=1)
        self.gs = gs


    def process(self, event):
        _tr = self.tr.copy()
        stacha = f'{_tr.stats.station} {_tr.stats.channel}'
        t2 = UTCDateTime(self.results[stacha]['t2'])
        t3 = UTCDateTime(self.results[stacha]['t3'])

        _tr.trim(t2, t3)

        factor = float(self.frm_process.factor_ent.get())

        freq, fft_norm, fft_smooth, peaks, f, a, q_f, q_alpha = get_peaks(
            _tr,
            float(self.frm_process.freqmin_ent.get()),
            float(self.frm_process.freqmax_ent.get()),
            int(self.frm_process.order_ent.get()),
            factor,
            distance_Hz=float(self.frm_process.distance_Hz_ent.get())
        )

        # Output
        self.results[stacha]['q_alpha'] = q_alpha
        self.results[stacha]['peaks'] = dict(
            frequency=f,
            amplitude=a,
            q_f=q_f,
            q_alpha=q_alpha
        )

        # Plot
        try:
            self.fig.get_axes()[3].remove()
        except:
            pass

        ax3 = self.fig.add_subplot(self.gs[1, 1], sharey=self.fig.get_axes()[2])
        ax3.clear()
        ax3.plot(fft_norm, freq, label='FFT')
        ax3.plot(factor*fft_smooth, freq, label=f'Smoothed FFT x{factor}')
        ax3.scatter(fft_norm[peaks], freq[peaks], marker='x',
                    label='Identified peak', s=50, c='r')
        ax3.yaxis.tick_right()
        ax3.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01))
        ax3.set_xticks([])
        ax3.set_xlabel('Normalized amplitude')
        self.canvas.draw()

    def overwrite_c(self):
        with open(CONF_FILEPATH, 'w') as f:
            json.dump(self.c, f, indent=4)
        tk.messagebox.showinfo(
            'Configuration saved',
            f'Current settings saved in the {CONF_FILEPATH} file'
        )


class Table:
    def __init__(self, parent, header, columns):
        font_size = 12
        width = 15

        for column, head in enumerate(header):
            self.e = tk.Entry(parent, width=width)
            self.e.grid(row=0, column=column)
            self.e.insert(tk.END, head)
            self.e.config(state='disabled', disabledforeground='black',
                          font=f'Arial {font_size} bold')

        for column, data in enumerate(columns):
            for row, datum in enumerate(data):
                self.e = tk.Entry(parent, width=width)
                self.e.grid(row=row+1, column=column)
                self.e.insert(tk.END, datum)
                self.e.config(state='disabled', disabledforeground='black',
                              font=f'Arial {font_size}')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = Root()
    root.mainloop()
