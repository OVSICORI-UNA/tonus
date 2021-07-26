#!/usr/bin/env python

# Python Standard Library
import importlib
import logging
import sys
import tkinter as tk
from tkinter import ttk

# Other dependencies
import matplotlib.pyplot as plt
from obspy import read, read_inventory
import pandas as pd
import psycopg2

# Local files
from tonus.config import set_conf, CONF_FILEPATH
from tonus.gui.coda import AppCoda
from tonus.gui.tremor import AppTremor
from tonus.gui.utils import open_window


# plt.style.use('dark_background')


class Root(tk.Tk):
    def __init__(self):
        super().__init__()

        self._set_conf()

        self.wm_title('tonus')

        # Style
        self.font_title = 'Helvetica 14 bold'
        self.bd = 1
        self.relief = tk.GROOVE

        self.frm_waveserver = self.FrameWaveServer(self)
        self.frm_waveserver.switch_waveserver()
        self.frm_inventory = self.FrameInventory(self)
        self.frm_portal = self.FramePortal(self)

        self.frm_waveserver.grid(row=0, column=0)
        self.frm_inventory.grid(row=1, column=0)
        self.frm_portal.grid(row=2, column=0)

        self.connect_waveserver()
        self.load_inventory()
        self.connect_database()

    def _set_conf(self):
        try:
            self.c = set_conf()
        except Exception as e:
            logging.error(e)
            text=(
                f'Configuration {CONF_FILEPATH} file missing. '
                'Copy it from tonus/ and modify it.'
            )
            tk.messagebox.showwarning('Configuration file missing', text)
            self.destroy()

    class FrameWaveServer(tk.LabelFrame):
        def __init__(self, master):
            super().__init__(
                master,
                text='Waveforms source',
                font=master.font_title,
                bd=master.bd,
                relief=master.relief,
                padx=10,
                pady=10
            )

            self.sv_waveserver = tk.StringVar(self)
            self.sv_waveserver.set(self.master.c.waveserver.client)
            self.rbtn_fdsn = tk.Radiobutton(
                self,
                text='FDSN',
                variable=self.sv_waveserver,
                value='fdsn',
                command=self.switch_waveserver
            )
            # self.rbtn_winston = tk.Radiobutton(
            #     self,
            #     text='Earthworm',
            #     value='earthworm',
            #     variable=self.sv_waveserver,
            #     command=self.switch_waveserver
            # )
            self.rbtn_files = tk.Radiobutton(
                self,
                text='files',
                value='files',
                variable=self.sv_waveserver,
                command=self.switch_waveserver
            )

            self.lbl_ip = tk.Label(self, text='IP')
            self.ent_ip = tk.Entry(self, width=14)
            self.ent_ip.insert(tk.END, self.master.c.waveserver.ip)

            self.lbl_port = tk.Label(self, text='Port')
            self.ent_port = tk.Entry(self, width=14)
            self.ent_port.insert(tk.END, self.master.c.waveserver.port)

            self.btn_waveserver_connect = tk.Button(
                self,
                text='Connect',
                command=self.master.connect_waveserver
            )


            self.lbl_files = tk.Label(self, text='Inventory')
            self.btn_files_select = tk.Button(
                self,
                text='Select waveform files',
                command=self.select_waves_files
            )



            self.rbtn_fdsn.grid(row=0, column=0, sticky='nw')
            # self.rbtn_winston.grid(row=0, column=1, sticky='nw')

            self.lbl_ip.grid(row=1, column=0, sticky='nw')
            self.ent_ip.grid(row=1, column=1, sticky='nw')

            self.rbtn_files.grid(row=3, column=0, sticky='nw')
            self.btn_files_select.grid(row=3, column=1, sticky='nw')

            self.lbl_port.grid(row=2, column=0, sticky='nw')
            self.ent_port.grid(row=2, column=1, sticky='nw')

            self.btn_waveserver_connect.grid(row=0, column=1)

        def switch_waveserver(self):
            self.master.c.waveserver.client = self.sv_waveserver.get()
            if self.sv_waveserver.get() in ['fdsn', 'earthworm']:
                self.ent_ip['state']   = 'normal'
                self.ent_port['state'] = 'normal'
                self.btn_waveserver_connect['state'] = 'normal'
                self.btn_files_select['state'] = 'disabled'
            elif self.sv_waveserver.get() == 'files':
                self.ent_ip['state']   = 'disabled'
                self.ent_port['state'] = 'disabled'
                self.btn_waveserver_connect['state'] = 'disabled'
                self.btn_files_select['state'] = 'normal'

        def select_waves_files(self):
            filepaths = list(
                tk.filedialog.askopenfilenames(title='Select waves files')
            )
            data = []
            for filepath in filepaths:
                try:
                    st = read(filepath, headonly=True)
                    for tr in st:
                        data.append(
                            dict(
                                filepath=filepath,
                                station=tr.stats.station,
                                channel=tr.stats.channel,
                                starttime=tr.stats.starttime.datetime,
                                endtime=tr.stats.endtime.datetime
                            )
                        )
                except Exception as e:
                    logging.error(e)
                    continue

            self.master.df_files = pd.DataFrame(data)


            if len(data) == 1:
                text = '1 file pre-loaded'
            else:
                text = f'{len(data)} files pre-loaded'
            tk.messagebox.showinfo('Files pre-loaded', text)

    class FrameInventory(tk.LabelFrame):
        def __init__(self, master):
            super().__init__(
                master,
                text='Inventory',
                font=master.font_title,
                bd=master.bd,
                relief=master.relief,
                padx=10,
                pady=10
            )
            self.ent_inventory = tk.Entry(self, width=24)
            self.ent_inventory.insert(tk.END, self.master.c.inventory)
            self.btn_inventory_select = tk.Button(
                self,
                text='Select inventory file',
                command=self.select_inventory_file
            )
            self.btn_inventory_load = tk.Button(
                self,
                text='Load inventory',
                command=self.master.load_inventory
            )

            self.btn_inventory_select.grid(row=0, column=0)
            self.ent_inventory.grid(row=1, column=0, columnspan=3)
            self.btn_inventory_load.grid(row=2, column=0)

        def select_inventory_file(self):
            filepath = tk.filedialog.askopenfilename(
                title='Open inventory/response file',
                initialdir=self.master.c.inventory,
            )
            self.ent_inventory.delete(0, 'end')
            self.ent_inventory.insert(tk.END, filepath)

    class FramePortal(tk.LabelFrame):
        def __init__(self, master):
            super().__init__(
                master,
                text='Select the type of signal to process',
                font=master.font_title,
                bd=master.bd,
                relief=master.relief,
            )
            self.btn_coda = tk.Button(
                self,
                text='Tonal coda',
                command=lambda: open_window(master, AppCoda(master))
            )
            self.btn_tremor = tk.Button(
                self,
                text='Harmonic tremor',
                command=lambda: open_window(master, AppTremor(master))
            )

            self.btn_coda.grid()
            self.btn_tremor.grid()

    class FramePortal(tk.LabelFrame):
        def __init__(self, master):
            super().__init__(
                master,
                text='Select the type of signal to process',
                font=master.font_title,
                bd=master.bd,
                relief=master.relief,
                padx=10,
                pady=10
            )
            self.btn_coda = tk.Button(
                self,
                text='Tonal coda',
                command=lambda: open_window(master, AppCoda(master))
            )
            self.btn_coda.grid()
            self.btn_tremor = tk.Button(
                self,
                text='Harmonic tremor',
                command=lambda: open_window(master, AppTremor(master))
            )
            self.btn_tremor.grid()


    def connect_waveserver(self):
        name = self.frm_waveserver.sv_waveserver.get()
        if name not in 'fdsn earthworm'.split():
            return


        ip   = self.frm_waveserver.ent_ip.get()
        port = self.frm_waveserver.ent_port.get()

        waveserver = importlib.import_module(f'obspy.clients.{name}')
        try:
            logging.info(f'Connecting to {ip}...')
            if name == 'fdsn':
                if ip == 'IRIS':
                    self.client = waveserver.Client(ip)
                else:
                    self.client = waveserver.Client(f'http://{ip}:{port}')
            elif name == 'earthworm':
                self.client = waveserver.Client(ip, int(port))
            logging.info(f'Succesfully connected to {ip} client.\n')
            return self.client
        except Exception as e:
            logging.error(e)
            tk.messagebox.showwarning('Warning', e)


    def load_inventory(self):
        logging.info('Loading inventory...')
        try:
            self.inventory = read_inventory(
                self.frm_inventory.ent_inventory.get()
            )
        except Exception as e:
            logging.error(e)
            tk.messagebox.showwarning('Warning', e)

    def connect_database(self):
        try:
            self.conn = psycopg2.connect(**self.c.db)
            logging.info('Succesfully connected to the database.')
        except Exception as e:
            logging.error(e)
            tk.messagebox.showwarning('Warning', e)


if __name__ == "__main__":
    from tonus.gui.queries import get_volcanoes_with_event

    database = {
        "host": "10.10.129.145",
        "user": "postgres",
        "password": "ovsicori84",
        "database": "tonus"
    }
    conn = psycopg2.connect(**database)

    print(get_volcanoes_with_event('tremor', conn)); exit()
