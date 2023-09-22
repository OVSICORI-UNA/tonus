# Python Standard Library
from datetime import datetime, timedelta
import tkinter as tk

# Other dependencies
import pandas as pd

# Local files
from tonus.gui.windows import WindowSpecSettings
from tonus.gui.utils import overwrite_c, open_window, download
from tonus.gui.windows import WindowPlotResults


class FrameWaves(tk.LabelFrame):
    def __init__(self, master):
        super().__init__(
            master,
            text='Waveforms',
            font=master.font_title,
            bd=master.bd,
            relief=master.relief,
        )
        width = 17

        # Volcano
        self.volcano_lbl = tk.Label(self, text='Volcano')
        self.get_volcanoes(master.conn)

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

        for channel in ['HHE', 'HHN', 'HHZ', 'HDF', 'BHZ']:
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
        self.swarm_lbx.config(
            yscrollcommand=self.swarm_sb.set, exportselection=False
        )
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
        self.duration_ent.insert(tk.END, self.master.c.waveforms.duration)

        self.download_btn = tk.Button(
            self,
            text='Get waveforms',
            command=lambda: download(master)
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
            self.master.conn
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
            initialdir=self.master.c.waveforms.swarm_dir,
            filetypes=filetypes
        )

        df = pd.read_csv(self.swarm_file, usecols=[0], names=['datetime'])
        self.swarm_lbx.delete(0, tk.END)
        for i, row in df.iterrows():
            self.swarm_lbx.insert(tk.END, row.datetime)


class FrameTraceSelection(tk.LabelFrame):
    def __init__(self, master):
        super().__init__(
            master,
            text='Select trace (next: f)',
            font=master.font_title,
            bd=master.bd,
            relief=master.relief,
        )

        self.stacha_lbx = tk.Listbox(self, height=3, exportselection=False)
        self.stacha_lbx.grid()
        self.stacha_lbx.bind('<<ListboxSelect>>', self.master._select_trace)


class FramePlot(tk.LabelFrame):
    def __init__(self, master, text):
        super().__init__(
            master,
            text=text,
            font=master.font_title,
            bd=master.bd,
            relief=master.relief,
        )


class FrameMenu(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.plot_results_btn = tk.Button(
            self,
            text='Plot database results',
            command=lambda: open_window(
                master, WindowPlotResults(master)
            )
        )
        self.plot_results_btn.grid(row=0, column=0)


        self.spec_cfg_btn = tk.Button(
            self,
            text='Spectrogram settings',
            command=lambda: open_window(master, WindowSpecSettings(master))
        )
        self.spec_cfg_btn.grid(row=0, column=1)


        self.overwrite_c_btn = tk.Button(
            self,
            text='Overwrite configuration',
            command=lambda: overwrite_c(self.master.c)
        )
        self.overwrite_c_btn.grid(row=0, column=2)


        self.quit_btn = tk.Button(
            self,
            text='Quit',
            command=self.master.destroy
        )
        self.quit_btn.grid(row=0, column=3)


class FrameOutput(tk.LabelFrame):
    def __init__(self, master):
        super().__init__(
            master,
            text='Output',
            font=master.font_title,
            bd=master.bd,
            relief=master.relief,
        )

        self.results_btn = tk.Button(
            self,
            text='View results & submit',
            command=lambda: open_window(master, master.WindowResults(master))
        )
        self.results_btn.pack()
