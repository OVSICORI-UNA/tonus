#!/usr/bin/env python


"""
"""


# Python Standard Library
import tkinter as tk

# Other dependencies
import matplotlib.pyplot as plt
import tonus

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'laat@umich.edu'


class WindowSpecSettings(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title('Spectrogram settings')

        quit_btn = tk.Button(self, text='Close', command=self._destroy)

        self.window_lf = tk.LabelFrame(self, text='Window')
        self.yaxis_lf = tk.LabelFrame(self, text='Y-axis')
        self.cmap_lf = tk.LabelFrame(self, text='Color map')

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
        self.per_lap_ent = tk.Entry(
            self.window_lf,
            textvariable=self.per_lap_svr
        )

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
        self.ymin_ent = tk.Entry(
            self.yaxis_lf, textvariable=self.ymin_svr, width=4
        )

        self.ymax_lbl = tk.Label(self.yaxis_lf, text='min(f) [Hz]')
        self.ymax_svr = tk.DoubleVar(self)
        self.ymax_svr.set(self.master.c.spectrogram.ymax)
        self.ymax_svr.trace(
            'w',
            lambda var, indx, mode: self.set_conf_change(
                var, indx, mode, 'ymax', self.ymax_svr.get()
            )
        )
        self.ymax_ent = tk.Entry(
            self.yaxis_lf, textvariable=self.ymax_svr, width=4
        )

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


class WindowSettings(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
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
            command=lambda: master.connect_waveserver(
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


class WindowPlotResults(tk.Toplevel):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.conn = master.conn
        self.title('Plot database results')
        self.event_type = master.event_type

        self.quit_btn = tk.Button(self, text='Close', command=self._destroy)
        self.selec_frm = self.FrameSelection(self, master.conn)

        self.plot_selec_frm = self.FramePlotSelection(self, master.conn)

        self.plot_db_lf = tk.LabelFrame(self, text='Plot')

        self.download_csv_btn = tk.Button(
            self,
            text='Export CSV',
            command=self.download_csv,
            state='disabled',
        )

        self.quit_btn.grid(row=0, column=0)
        self.selec_frm.grid(row=1, column=0)
        self.download_csv_btn.grid(row=2, column=0)
        self.plot_selec_frm.grid(row=3, column=0)
        self.plot_db_lf.grid(row=0, column=1, rowspan=self.grid_size()[1]+1)

    class FrameSelection(tk.LabelFrame):
        def __init__(self, master, conn):
            super().__init__(master, text='1. Data Selection')
            self.conn = conn
            self.event_type = master.event_type

            self.volcano_lbl = tk.Label(self, text='Volcano')
            self.volcano_lbl.pack()

            volcanoes = tonus.gui.queries.get_volcanoes_with_event(
                self.event_type,
                self.conn
            )
            if len(volcanoes) == 0:
                return

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
                text='Query',
                command=self.download_db,
                state='disabled'
            )
            self.download_db_btn.pack()

        def get_stacha(self, event):
            volcano = self.volcanoes_sv.get()

            stations, channels, ids = tonus.gui.queries.get_stacha_with_event(
                volcano, self.event_type, self.conn
            )

            self.stacha_lbx.delete(0, tk.END)
            for station, channel, channel_id in zip(stations, channels, ids):
                self.stacha_lbx.insert(
                    tk.END, f'{station} {channel} {channel_id}'
                )
            if len(stations) > 0:
                self.download_db_btn['state'] = 'normal'

        def download_db(self):
            selection = self.stacha_lbx.curselection()
            stachas = [self.stacha_lbx.get(s) for s in selection]
            channel_ids = [stacha.split()[2] for stacha in stachas]

            self.master.df, self.master.hist = tonus.gui.queries.get_data(
                channel_ids, self.event_type, self.conn
            )

            self.master.plot_selec_frm.stacha_lbx.delete(0, tk.END)
            for stacha in self.master.df.stacha.unique():
                self.master.plot_selec_frm.stacha_lbx.insert(tk.END, stacha)

            self.master.download_csv_btn['state'] = 'normal'
            self.master.plot_selec_frm.plot_btn['state'] = 'normal'

    class FramePlotSelection(tk.LabelFrame):
        def __init__(self, master, conn):
            super().__init__(master, text='2. Plotting')
            self.conn = conn
            self.event_type = master.event_type

            self.stacha_lbl = tk.Label(self, text='Channel(s)')
            self.stacha_lbl.pack()
            self.stacha_lbx = tk.Listbox(self, selectmode=tk.MULTIPLE,
                                         height=3)
            self.stacha_lbx.pack()

            self.plot_btn = tk.Button(
                self,
                text='Plot',
                command=self.plot,
                state='disabled'
            )
            self.plot_btn.pack()

        def plot(self):
            # Filter by station/channel selection
            selection = self.stacha_lbx.curselection()
            stachas = [self.stacha_lbx.get(s) for s in selection]
            channel_ids = [int(stacha.split()[2]) for stacha in stachas]
            df = self.master.df
            df = df[df.channel_id.isin(channel_ids)]

            hist = self.master.hist
            hist = hist[hist.channel_id.isin(channel_ids)]
            hist = hist.groupby('id').min()
            # hist.index = hist.starttime.dt.tz_convert('America/Guatemala')
            hist.index = hist.starttime
            hist = hist.drop(hist.columns[:-1], axis=1)
            hist.columns = ['n']
            window = 'D'
            if (hist.index.max() - hist.index.min()).days > 365:
                window = 'W'
            hist = hist.resample(window).count()

            self.fig = tonus.gui.plotting.plot_db(df, hist, self.event_type)

            self.canvas = FigureCanvasTkAgg(
                self.fig, master=self.master.plot_db_lf
            )
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


if __name__ == '__main__':
    pass
