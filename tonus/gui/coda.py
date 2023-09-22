#!/usr/bin/env python


"""
"""


# Python Standard Library
import logging
import tkinter as tk

# Other dependencies
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tonus

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)
from matplotlib.backend_bases import key_press_handler
from matplotlib.widgets import MultiCursor
from obspy import UTCDateTime

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'laat@umich.edu'


class AppCoda(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.c = master.c
        self.client = master.client
        self.conn = master.conn
        self.inventory = master.inventory
        if hasattr(master, 'df_files'):
            self.df_files = master.df_files
        self.event_type = 'coda'

        self.wm_title('tonus - tonal coda')
        self.font_title = master.font_title
        self.bd = master.bd
        self.relief = master.relief

        # Menu bar
        self.menubar = tonus.gui.frames.FrameMenu(self)

        txt = (
            'Pick with right-click button 3 times'
            ': 1. event start; 2. coda start; and 3. coda end.'
        )
        # Frames initiation
        self.frm_waves = tonus.gui.frames.FrameWaves(self)
        self.frm_tr_select = tonus.gui.frames.FrameTraceSelection(self)
        self.frm_plt = tonus.gui.frames.FramePlot(
            self, txt
        )
        self.frm_process = self.FrameProcess(self)
        self.frm_output = tonus.gui.frames.FrameOutput(self)

        # Frames gridding
        self.menubar.grid(row=0, column=0, sticky='nw', columnspan=2)
        self.frm_waves.grid(row=1, column=0, sticky='nw')
        self.frm_tr_select.grid(row=2, column=0, sticky='nw')
        self.frm_plt.grid(row=1, column=1, rowspan=self.grid_size()[1]+2)
        self.frm_process.grid(row=3, column=0, sticky='nw')
        self.frm_output.grid(row=4, column=0, sticky='nw')

        # Shortcut-keys
        self.bind('<r>', self.process)
        self.bind('<f>', self.select_next_trace)

    class FrameProcess(tk.LabelFrame):
        def __init__(self, master):
            super().__init__(
                master,
                text='Process',
                font=master.font_title,
                bd=master.bd,
                relief=master.relief,
            )
            validatefloat = self.register(tonus.gui.utils.isfloat)

            width = 4

            self.filter_lf = tk.LabelFrame(
                self,
                text='Butterworth bandpass filter',
            )

            self.freqmin_lbl = tk.Label(self.filter_lf, text='min(f) [Hz]')
            self.freqmin_svr = tk.DoubleVar(self)
            self.freqmin_svr.set(self.master.c.process.coda.freqmin)
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
            self.freqmax_svr.set(self.master.c.process.coda.freqmax)
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
            self.order_svr.set(self.master.c.process.coda.order)
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
            self.factor_svr.set(self.master.c.process.coda.factor)
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
            self.distance_Hz_svr.set(self.master.c.process.coda.distance_Hz)
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
                command=lambda: master.process('')
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
                self.master.c.process.coda.__setitem__(key, tkvar.get())
            except Exception as e:
                print(e)
                pass

    class WindowResults(tk.Toplevel):
        def __init__(self, master):
            super().__init__()
            self.master = master
            self.title('Output')

            self.quit_btn = tk.Button(
                self, text='Close', command=self._destroy
            )

            self.peaks_lf = tk.LabelFrame(self, text='Peaks detected')

            self.channels_lbl = tk.Label(self, text='Channels processed')
            self.channels_lbx = tk.Listbox(self, height=3)
            self.channels_lbx.delete(0, tk.END)
            self.channels_lbx.bind("<<ListboxSelect>>", self.create_table)
            try:
                for stacha in master.results:
                    if 'peaks' in master.results[stacha].keys():
                        self.channels_lbx.insert(tk.END, stacha)
                self.channels_lbx.select_set(0)
                self.channels_lbx.event_generate('<<ListboxSelect>>')
                self.channels_lbx.focus_set()
            except Exception as e:
                print(e)
                pass

            header = ['Frequency [Hz]', 'Relative amplitude', 'Q']

            tonus.gui.utils.Table(self.peaks_lf, header, [])

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

        def _destroy(self):
            self.master.focus_force()
            self.destroy()

        def create_table(self, event):
            selection = self.channels_lbx.curselection()
            if len(selection) < 1:
                return
            stacha = self.channels_lbx.get(selection[0])

            header = ['Frequency [Hz]', 'Relative amplitude', 'Q']

            frequency = [
                round(f, 2) for f in
                self.master.results[stacha]['peaks']['frequency']
            ]

            amplitude = [
                a for a in self.master.results[stacha]['peaks']['amplitude']
            ]
            amplitude = np.array(amplitude)
            amplitude /= amplitude.max()
            amplitude = np.round(amplitude, decimals=3)

            q_f = [
                round(q, 0) for q in
                self.master.results[stacha]['peaks']['q_f']
            ]
            columns = [frequency, amplitude, q_f]

            for widget in self.peaks_lf.winfo_children():
                widget.destroy()

            tonus.gui.utils.Table(self.peaks_lf, header, columns)

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
                cur.execute(
                    f"SELECT id FROM volcano WHERE volcano = '{volcano}';"
                )
                volcano_id = cur.fetchone()[0]

                starttimes, endtimes = [], []
                for stacha in self.master.results.keys():
                    starttimes.append(
                        UTCDateTime(self.master.results[stacha]['t1'])
                    )
                    endtimes.append(
                        UTCDateTime(self.master.results[stacha]['t3'])
                    )
                starttime = min(starttimes).datetime
                endtime = max(endtimes).datetime

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
                    coda(channel_id, t1, t2, t3, event_id, q_alpha)
                VALUES(
                    {channel_id}, '{t1}', '{t2}', '{t3}',
                    {self.master.event_id}, {q_alpha}
                )
                RETURNING
                    id
                """
                try:
                    cur.execute(sql_str)
                    coda_id = cur.fetchone()[0]

                    freq = self.master.results[stacha]['peaks']['frequency']
                    ampl = self.master.results[stacha]['peaks']['amplitude']
                    q_f = self.master.results[stacha]['peaks']['q_f']

                    for f, a, q in zip(freq, ampl, q_f):
                        cur.execute(
                            f"""
                            INSERT INTO
                                coda_peaks(coda_id, frequency,
                                amplitude, q_f)
                            VALUES(
                                {coda_id}, {round(f, 3)},
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
        SELECT
            event.* FROM event
        INNER JOIN
            volcano
        ON
            event.volcano_id = volcano.id
        AND
            volcano.volcano = '{volcano}'
        AND
            (starttime BETWEEN timestamp '{self.starttime.datetime}'
            and timestamp '{self.endtime.datetime}');
        """

        df = pd.read_sql_query(query, self.conn)

        if len(df) > 0:
            self.event_id = df.id.to_list()[0]

            df = pd.read_sql_query(
                f"""
                SELECT * FROM coda
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
                stachas = ', '.join([
                    f'{row.station} {row.channel}' for i, row in df.iterrows()
                ])

                text = (
                    'There is already an analysed event '
                    f'(ID = {self.event_id}), '
                    f'in the time range requested '
                    f'in stations/channels: {stachas}. '
                    f'Do not process this channels, else any new results from '
                    'other channels will not be submitted. '
                )
                tk.messagebox.showwarning('Event already analysed', text)
            else:
                text = (
                    f'There is already an event (ID = {self.event_id}) in the '
                    'database in the time range requested, '
                    'but not analysed yet. '
                    'Any further results will be associated to this event.'
                )
                tk.messagebox.showwarning('Event in database', text)
        else:
            self.event_id = None

    def _select_trace(self, event):
        tonus.gui.utils.select_trace(self)

    def select_next_trace(self, event):
        selected_trace = self.frm_tr_select.stacha_lbx.curselection()[0]
        n_traces = self.frm_tr_select.stacha_lbx.size()

        if selected_trace < n_traces-1:
            self.frm_tr_select.stacha_lbx.selection_clear(0, tk.END)
            self.frm_tr_select.stacha_lbx.select_set(selected_trace+1)
            self.frm_tr_select.stacha_lbx.event_generate('<<ListboxSelect>>')
        else:
            tonus.gui.utils.open_window(self, self.WindowResults(self))

    def plot(self):
        tr = self.tr.copy()
        tr.data = tr.data * 1e6
        stacha = f'{tr.stats.station} {tr.stats.channel}'

        # time_str = str(tr.stats.starttime)[:-8].replace('T', ' ')

        time = np.arange(
            0, tr.stats.npts/tr.stats.sampling_rate, tr.stats.delta
        )
        if len(time) > len(tr.data):
            time = time[:-1]

        self.fig = plt.figure(figsize=(8, 6))

        self.fig.subplots_adjust(
            left=.09, bottom=.07, right=.94, top=0.962, wspace=.04, hspace=.12
        )

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
        _ax1.set_ylabel(r'Amplitude [$\mu m/s$]')

        ax2 = self.fig.add_subplot(gs[1, 0], sharex=ax1)
        tonus.gui.plotting.spectrogram(self.c, tr, ax2)
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
            except Exception as e:
                print(e)
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

        (
            freq, fft_norm, fft_smooth, peaks, f, a, q_f, q_alpha
        ) = tonus.process.coda.get_peaks(
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
        except Exception as e:
            print(e)

        ax3 = self.fig.add_subplot(
            self.gs[1, 1], sharey=self.fig.get_axes()[2]
        )
        ax3.clear()
        ax3.plot(fft_norm, freq, label='FFT')
        ax3.plot(factor*fft_smooth, freq, label=f'Smoothed FFT x{factor}')
        ax3.scatter(
            fft_norm[peaks],
            freq[peaks],
            marker='x',
            label='Identified peak',
            s=50,
            c='r'
        )
        ax3.yaxis.tick_right()
        ax3.legend(loc='lower left', bbox_to_anchor=(0.0, 1.01))
        ax3.set_xticks([])
        ax3.set_xlabel('Normalized amplitude')
        self.canvas.draw()


if __name__ == '__main__':
    pass
