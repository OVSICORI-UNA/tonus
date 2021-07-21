# Python Standard Library
import logging
import tkinter as tk

# Other dependencies
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)
from matplotlib.backend_bases import key_press_handler
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
import numpy as np
from obspy import UTCDateTime
import pandas as pd

# Local files
from tonus.gui import frames
from tonus.gui.utils import isfloat, open_window, select_trace
from tonus.gui.plotting import spectrogram
from tonus.gui.queries import get_volcanoes_with_event, get_stacha_with_event
from tonus.preprocess import butter_bandpass_filter
from tonus.process.tremor import detect_f1, get_harmonics


class AppTremor(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.c = master.c
        self.client = master.client
        self.conn = master.conn
        self.inventory = master.inventory
        if hasattr(master, 'df_files'):
            self.df_files = master.df_files
        self.event_type = 'tremor'

        self.wm_title('tonus - harmonic tremor')
        self.font_title = master.font_title
        self.bd         = master.bd
        self.relief     = master.relief

        # Menu bar
        self.menubar = frames.FrameMenu(self)

        # Frames initiation
        self.frm_waves     = frames.FrameWaves(self)
        self.frm_tr_select = frames.FrameTraceSelection(self)
        self.frm_plt       = frames.FramePlot(
            self, 'Pick only in case of pre-tremor LP'
        )
        self.frm_process = self.FrameProcess(self)
        self.frm_output   = frames.FrameOutput(self)

        # Frames gridding
        self.menubar.grid(row=0, column=0, sticky='nw', columnspan=3)
        self.frm_waves.grid(row=1, column=0, sticky='nw')
        self.frm_tr_select.grid(row=2, column=0, sticky='nw')

        self.frm_plt.grid(row=1, column=1, rowspan=self.grid_size()[1]+2)

        self.frm_process.grid(row=1, column=2, sticky='ne')
        self.frm_output.grid(row=2, column=2, sticky='ne')

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
            validatefloat = self.register(isfloat)

            width = 4

            self.filter_lf= tk.LabelFrame(self, text='Bandpass filter',)

            self.lbl_freqmin = tk.Label(self.filter_lf, text='min(f) [Hz]')
            self.freqmin_svr = tk.DoubleVar(self)
            self.freqmin_svr.set(self.master.c.process.tremor.freqmin)
            self.freqmin_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'freqmin', self.freqmin_svr
                )
            )
            self.ent_freqmin = tk.Entry(
                self.filter_lf, textvariable=self.freqmin_svr, width=width,
                validate='all', validatecommand=(validatefloat, '%P'),
            )

            self.freqmax_lbl = tk.Label(self.filter_lf, text='max(f) [Hz]')
            self.freqmax_svr = tk.DoubleVar(self)
            self.freqmax_svr.set(self.master.c.process.tremor.freqmax)
            self.freqmax_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'freqmax', self.freqmax_svr
                )
            )
            self.ent_freqmax = tk.Entry(
                self.filter_lf, textvariable=self.freqmax_svr, width=width,
                validate='all', validatecommand=(validatefloat, '%P'),
            )

            self.order_lbl = tk.Label(self.filter_lf, text='Order')
            self.order_svr = tk.IntVar(self)
            self.order_svr.set(self.master.c.process.tremor.order)
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

            self.lf_window= tk.LabelFrame(self, text='Windowing',)
            self.lbl_window_length = tk.Label(self.lf_window, text='Length [s]')
            self.svr_window_length = tk.DoubleVar(self)
            self.svr_window_length.set(self.master.c.process.tremor.window_length)
            self.svr_window_length.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'window_length', self.svr_window_length
                )
            )
            self.ent_window_length = tk.Entry(
                self.lf_window, textvariable=self.svr_window_length,
                width=width, validate='all',
                validatecommand=(validatefloat, '%P'),
            )

            self.lbl_overlap = tk.Label(self.lf_window, text='Overlap fraction')
            self.svr_overlap = tk.DoubleVar(self)
            self.svr_overlap.set(self.master.c.process.tremor.overlap)
            self.svr_overlap.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'overlap', self.svr_overlap
                )
            )
            self.ent_overlap = tk.Entry(
                self.lf_window, textvariable=self.svr_overlap,
                width=width, validate='all',
                validatecommand=(validatefloat, '%P'),
            )

            self.lf_yin = tk.LabelFrame(self, text='Yin',)
            self.lbl_thresh = tk.Label(self.lf_yin, text='Threshold')
            self.svr_thresh = tk.DoubleVar(self)
            self.svr_thresh.set(self.master.c.process.tremor.thresh)
            self.svr_thresh.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'thresh', self.svr_overlap
                )
            )
            self.ent_thresh = tk.Entry(
                self.lf_yin, textvariable=self.svr_thresh,
                width=width, validate='all',
                validatecommand=(validatefloat, '%P'),
            )

            self.lf_harmonics = tk.LabelFrame(self, text='Harmonics detection',)
            self.lbl_n_harmonics_max = tk.Label(
                self.lf_harmonics, text='max(n(harmonics))')

            self.svr_n_harmonics_max = tk.IntVar(self)
            self.svr_n_harmonics_max.set(
                self.master.c.process.tremor.n_harmonics_max
            )
            self.svr_n_harmonics_max.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'n_harmonics_max', self.svr_n_harmonics_max
                )
            )
            self.ent_n_harmonics_max = tk.Entry(
                self.lf_harmonics, textvariable=self.svr_n_harmonics_max,
                width=width, validate='all',
                validatecommand=(validatefloat, '%P'),
            )


            self.lbl_band_width_Hz = tk.Label(
                self.lf_harmonics, text='Band width [Hz]')

            self.svr_band_width_Hz = tk.IntVar(self)
            self.svr_band_width_Hz.set(
                self.master.c.process.tremor.band_width_Hz
            )
            self.svr_band_width_Hz.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'band_width_Hz', self.svr_band_width_Hz
                )
            )
            self.ent_band_width_Hz = tk.Entry(
                self.lf_harmonics, textvariable=self.svr_band_width_Hz,
                width=width, validate='all',
                validatecommand=(validatefloat, '%P'),
            )


            self.factor_lbl = tk.Label(self.lf_harmonics, text='Threshold')
            self.factor_svr = tk.IntVar(self)
            self.factor_svr.set(self.master.c.process.tremor.factor)
            self.factor_svr.trace(
                'w',
                lambda var, indx, mode: self.set_conf_change(
                    var, indx, mode, 'factor', self.factor_svr
                )
            )
            self.factor_ent = tk.Entry(
                self.lf_harmonics, textvariable=self.factor_svr, width=width,
                validate='all', validatecommand=(validatefloat, '%P'),
            )


            self.process_btn = tk.Button(
                self,
                text='Process',
                command=lambda: master.process('')
            )

            self.filter_lf.grid(row=0, column=0, columnspan=2)
            self.lf_window.grid(row=1, column=0, columnspan=2)
            self.lf_yin.grid(row=2, column=0, columnspan=2)
            self.lf_harmonics.grid(row=3, column=0, columnspan=2)
            self.process_btn.grid(row=4, column=0, columnspan=2)

            # Filter
            self.lbl_freqmin.grid(row=0, column=0)
            self.ent_freqmin.grid(row=0, column=1)
            self.freqmax_lbl.grid(row=1, column=0)
            self.order_lbl.grid(row=2, column=0)
            self.ent_freqmax.grid(row=1, column=1)
            self.order_ent.grid(row=2, column=1)

            # Yin
            self.lbl_thresh.grid(row=0, column=0)
            self.ent_thresh.grid(row=0, column=1)

            # Windowing
            self.lbl_window_length.grid(row=0, column=0)
            self.ent_window_length.grid(row=0, column=1)
            self.lbl_overlap.grid(row=1, column=0)
            self.ent_overlap.grid(row=1, column=1)

            # Harmonics detection
            self.factor_lbl.grid(row=0, column=0)
            self.factor_ent.grid(row=0, column=1)
            self.lbl_n_harmonics_max.grid(row=1, column=0)
            self.ent_n_harmonics_max.grid(row=1, column=1)
            self.lbl_band_width_Hz.grid(row=2, column=0)
            self.ent_band_width_Hz.grid(row=2, column=1)


        def set_conf_change(self, var, indx, mode, key, tkvar):
            try:
                self.master.c.process.tremor.__setitem__(key, tkvar.get())
            except:
                pass

    class WindowResults(tk.Toplevel):
        def __init__(self, master):
            super().__init__()
            self.master = master
            self.title('Output')

            self.quit_btn = tk.Button(self, text='Close', command=self._destroy)

            self.lf_summary = tk.LabelFrame(self, text='Summary')

            self.channels_lbl = tk.Label(self, text='Channels processed')
            self.channels_lbx = tk.Listbox(self, height=3)
            self.channels_lbx.delete(0, tk.END)
            self.channels_lbx.bind("<<ListboxSelect>>", self.create_table)
            try:
                for stacha in master.results:
                    if 'fmean' in master.results[stacha].keys():
                        self.channels_lbx.insert(tk.END, stacha)
                self.channels_lbx.select_set(0)
                self.channels_lbx.event_generate('<<ListboxSelect>>')
                self.channels_lbx.focus_set()
            except:
                pass

            table = Table(self.lf_summary, [])

            self.submit_btn = tk.Button(
                self,
                text='Submit',
                command=self.submit
            )

            self.quit_btn.grid(row=0)
            self.channels_lbl.grid(row=1)
            self.channels_lbx.grid(row=2)
            self.lf_summary.grid(row=3)
            self.submit_btn.grid(row=4)

        def _destroy(self):
            self.master.focus_force()
            self.destroy()

        def create_table(self, event):
            selection = self.channels_lbx.curselection()
            if len(selection) < 1:
                return
            stacha = self.channels_lbx.get(selection[0])

            r = self.master.results[stacha]

            lp = 'No'
            if r['lp']:
                lp = 'Yes'

            keys = [
                'Duration [s]',
                'Mean fundamental frequency [Hz]',
                'Fundamental frequency change [Hz]',
                'Number of harmonics',
                'Harmonics',
                'LP-HT'
            ]
            values = [
                int(UTCDateTime(r['endtime']) - UTCDateTime(r['starttime'])),
                round(r['fmean'], 2),
                round(r['fmax'] - r['fmin'], 2),
                r['n_harmonics'],
                ', '.join(str(h) for h in r['harmonics']),
                lp
            ]
            for widget in self.lf_summary.winfo_children():
                widget.destroy()

            table = Table(self.lf_summary, [keys, values])

        def submit(self):
            submitted = False

            cur = self.master.conn.cursor()

            # Clean channels not picked
            results = {}
            for stacha in self.master.results.keys():
                if 'fmean' in self.master.results[stacha].keys():
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
                    if self.master.results[stacha]['lp']:
                        starttimes.append(
                            UTCDateTime(self.master.results[stacha]['lp_time'])
                        )
                    else:
                        starttimes.append(
                            UTCDateTime(self.master.results[stacha]['starttime'])
                        )
                    endtimes.append(
                        UTCDateTime(self.master.results[stacha]['endtime'])
                    )
                starttime = min(starttimes).datetime
                endtime   = max(endtimes).datetime

                sql_str = f"""
                INSERT INTO
                    event(starttime, endtime, volcano_id)
                VALUES
                    ('{starttime}', '{endtime}', {volcano_id})
                RETURNING
                    id
                """
                cur.execute(sql_str)
                self.master.event_id = cur.fetchone()[0]

            for stacha in self.master.results.keys():
                station, channel = stacha.split()
                cur.execute(
                   f"""
                    SELECT
                        id
                    FROM
                        channel
                    WHERE
                        channel = '{channel}'
                    AND
                        station = '{station}';
                    """
                )
                channel_id = cur.fetchone()[0]

                lp = self.master.results[stacha]['lp']
                if lp:
                    lp_time = "\'"+str(
                        UTCDateTime(self.master.results[stacha]['lp_time'])
                    )+"\'"
                else:
                    lp_time = 'NULL'
                starttime = UTCDateTime(self.master.results[stacha]['starttime']).datetime
                endtime = UTCDateTime(self.master.results[stacha]['endtime']).datetime
                fmin = self.master.results[stacha]['fmin']
                fmax = self.master.results[stacha]['fmax']
                fmean = self.master.results[stacha]['fmean']
                fstd = self.master.results[stacha]['fstd']
                fmedian = self.master.results[stacha]['fmedian']
                n_harmonics = self.master.results[stacha]['n_harmonics']
                harmonics = ', '.join(
                    str(h) for h in self.master.results[stacha]['harmonics']
                )

                harmonics = "\'{" +  harmonics + "}\'"
                amplitude = self.master.results[stacha]['amplitude']
                odd = self.master.results[stacha]['odd']

                sql_str = f"""
                INSERT INTO
                    tremor(event_id, channel_id, starttime, endtime,
                    fmin, fmax, fmean, fstd, fmedian, n_harmonics, amplitude,
                    lp_time, lp, odd, harmonics
                    )
                VALUES(
                    {self.master.event_id}, {channel_id}, '{starttime}',
                    '{endtime}', {fmin}, {fmax}, {fmean}, {fstd}, {fmedian},
                    {n_harmonics}, {amplitude}, {lp_time}, {lp}, {odd},
                    {harmonics}
                );
                """
                try:
                    cur.execute(sql_str)
                    submitted = True
                except Exception as e:
                    print(e)
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
                SELECT
                    *
                FROM
                    tremor
                WHERE
                    event_id = {self.event_id};
                """,
                self.conn
            )
            if len(df) > 0:
                channel_ids = ', '.join(str(c) for c in df.channel_id.tolist())

                query = f"""
                SELECT
                    station, channel
                FROM
                    channel
                WHERE
                    id
                IN
                    ({channel_ids})
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

    def _select_trace(self, event):
        select_trace(self)

    def select_next_trace(self, event):
        selected_trace = self.frm_tr_select.stacha_lbx.curselection()[0]
        n_traces = self.frm_tr_select.stacha_lbx.size()

        if selected_trace < n_traces-1:
            self.frm_tr_select.stacha_lbx.selection_clear(0, tk.END)
            self.frm_tr_select.stacha_lbx.select_set(selected_trace+1)
            self.frm_tr_select.stacha_lbx.event_generate('<<ListboxSelect>>')
        else:
            open_window(self, self.WindowResults(self))

    def plot(self):
        tr = self.tr.copy()
        tr.data = tr.data*1e9

        stacha = f'{tr.stats.station} {tr.stats.channel}'

        time_str = str(tr.stats.starttime)[:-8].replace('T',' ')

        time = np.arange(
            0, tr.stats.npts/tr.stats.sampling_rate, tr.stats.delta
        )
        if len(time) > len(tr.data):
            time = time[:-1]

        self.fig = plt.figure(figsize=(8, 5))

        self.fig.subplots_adjust(
            left=.07, bottom=.07, right=.95, top=0.962, wspace=.04, hspace=.12
        )

        gs = gridspec.GridSpec(nrows=3, ncols=1, height_ratios=[1, 4, 4])

        _ax1 = self.fig.add_subplot(gs[0, 0])

        ax1 = self.fig.add_subplot(gs[0, 0], zorder=2)
        ax1.plot(time, tr.data, linewidth=0.7)
        ax1.set_xlim(time.min(), time.max())

        ax1.axis("off")

        # Re-scale with zoom
        _ax1.set_navigate(False)
        _ax1.set_xlim(ax1.get_xlim())
        _ax1.set_ylim(ax1.get_ylim())
        _ax1.set_ylabel('Amplitude [nm/s]')

        self.ax2 = self.fig.add_subplot(gs[1, 0], sharex=ax1)
        spectrogram(self.c, tr, self.ax2)
        self.ax2.set_ylabel('Frequency [Hz]')
        self.ax2.set_xlabel('Time [s]')


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

        if stacha in self.results.keys():
            if 'lp' in self.results[stacha].keys():
                self.count += 1
                for ax in ax1, self.ax2:
                    xdata = UTCDateTime(
                        self.results[stacha]['lp']
                    ) - tr.stats.starttime
                    ax.axvline(x=xdata, linewidth=1, c='r', ls='--')

        self.results[stacha]['lp'] = False
        def _pick(event):
            if event.button == 3:
                if self.count < 1:
                    for ax in [ax1, self.ax2]:
                        ax.axvline(x=event.xdata, linewidth=1, c='r', ls='--')
                        self.canvas.draw()
                    t = tr.stats.starttime + event.xdata
                    logging.info(f'Time picked: {t}')
                    self.results[stacha]['lp'] = True
                    self.results[stacha]['lp_time'] = str(t)

                self.count += 1

        self.fig.canvas.mpl_connect('button_press_event', _pick)

        self.multi = MultiCursor(
            self.fig.canvas, (ax1, self.ax2), color='r', lw=1
        )
        self.gs = gs

    def process(self, event):
        window_s        = float(self.frm_process.ent_window_length.get())
        overlap         = float(self.frm_process.ent_overlap.get())
        freqmin         = float(self.frm_process.ent_freqmin.get())
        freqmax         = float(self.frm_process.ent_freqmax.get())
        order           = int(self.frm_process.order_ent.get())
        thresh          = float(self.frm_process.ent_thresh.get())
        n_harmonics_max = int(self.frm_process.ent_n_harmonics_max.get())
        band_width_Hz   = float(self.frm_process.ent_band_width_Hz.get())
        factor          = float(self.frm_process.factor_ent.get())

        _tr = self.tr.copy()
        stacha = f'{_tr.stats.station} {_tr.stats.channel}'
        _tr.detrend()
        butter_bandpass_filter(_tr, freqmin, freqmax, order)

        tau, t, pitch = detect_f1(_tr, window_s, overlap, freqmin, thresh)

        number, time, frequency, amplitude = get_harmonics(
            _tr,
            t,
            pitch,
            window_s,
            overlap,
            n_harmonics_max,
            band_width_Hz,
            factor,
            freqmin,
        )

        df = pd.DataFrame(
            list(zip(number, time, frequency, amplitude)),
            columns=['number', 'time', 'frequency', 'amplitude']
        )
        if len(df) == 0:
            return

        groups = df.groupby('number')
        df_f1 = df[df.number == 1]

        self.results[stacha]['starttime'] = df.time.min()
        self.results[stacha]['endtime']   = df.time.max()

        tr_amp = self.tr.slice(df.time.min(), df.time.max())
        self.results[stacha]['amplitude'] = np.sqrt((tr_amp.data**2).mean())

        self.results[stacha]['fmin'] = df_f1.frequency.min()
        self.results[stacha]['fmax'] = df_f1.frequency.max()
        self.results[stacha]['fmean'] = df_f1.frequency.mean()
        self.results[stacha]['fstd'] = df_f1.frequency.std()
        self.results[stacha]['fmedian'] = df_f1.frequency.median()

        harmonics = sorted(df.number.unique().tolist())
        self.results[stacha]['n_harmonics'] = len(harmonics)
        self.results[stacha]['harmonics'] = harmonics
        odd = True
        for harmonic in harmonics:
            if harmonic % 2 == 0:
                odd = False
        self.results[stacha]['odd'] = odd


        # Plot
        amin = df.amplitude.min()
        amax = df.amplitude.max()
        smin = 0.5
        smax = 1.5
        s = [smin+a*(smax-smin)/(amax-amin) for a in df.amplitude]
        df['linewidth'] = s

        try:
            self.ax3.remove()
            self.ax4.remove()
        except:
            pass


        self.ax3 = self.ax2.twinx()
        self.ax2.get_shared_y_axes().join(self.ax2, self.ax3)
        self.ax3.axis("off")
        self.ax3.set_ylim(self.c.spectrogram.ymin, self.c.spectrogram.ymax)

        self.ax4 = self.fig.add_subplot(
            self.gs[2, 0],
            sharex=self.ax2,
            sharey=self.ax2
        )
        self.ax4.set_xlabel('Time [s]')
        self.ax4.set_ylabel('Frequency [Hz]')

        self.ax3.plot(t, pitch, c='b', lw=1)

        start = df.time.min() - self.tr.stats.starttime
        end   = df.time.max() - self.tr.stats.starttime

        if start:
            self.ax3.axvline(start, c='b', lw=1, ls='--')
            self.ax4.axvline(start, c='b', lw=1, ls='--')
        if end:
            self.ax3.axvline(end, c='b', lw=1, ls='--')
            self.ax4.axvline(end, c='b', lw=1, ls='--')

        for n in range(n_harmonics_max, 0, -1):
            try:
                _df = groups.get_group(n)
            except Exception as e:
                continue

            _times = [t-self.tr.stats.starttime for t in _df.time]
            xy     = (_times[-1], _df.frequency.tolist()[-1])
            xytext = (_times[-1]+20, _df.frequency.tolist()[-1])

            self.ax3.scatter(
                _times,
                _df.frequency,
                marker='o',
                lw=_df.linewidth,
                c='w',
                s=_df.linewidth,
                alpha=0.7
            )
            self.ax3.annotate(
                '$\mathdefault{f_{'+str(n)+'}}$',
                xy=xy,
                xytext=xytext,
                arrowprops=dict(arrowstyle='->', color='k'),
                size=10,
                va='center',
                color='k',
                bbox=dict(boxstyle='round', fc='0.8')
            )
            self.ax4.scatter(
                _times,
                _df.frequency,
                marker='o',
                lw=_df.linewidth,
                s=_df.linewidth,
                alpha=0.7
            )
            self.ax4.annotate(
                '$\mathdefault{f_{'+str(n)+'}}$',
                xy=xy,
                xytext=xytext,
                arrowprops=dict(arrowstyle='->'),
                size=10,
                va='center',
                color='k',
                bbox=dict(boxstyle='round', fc='0.8')
            )
        self.canvas.draw()


class Table:
    def __init__(self, master, columns):
        font_size = 12

        for column, data in enumerate(columns):
            if column == 0:
                width = 30
            else:
                width = max(len(str(d))+3 for d in data)
            for row, datum in enumerate(data):
                self.e = tk.Entry(master, width=width)
                self.e.grid(row=row+1, column=column)
                self.e.insert(tk.END, datum)
                self.e.config(
                    state='disabled',
                    disabledforeground='black',
                    font=f'Arial {font_size}'
                )
