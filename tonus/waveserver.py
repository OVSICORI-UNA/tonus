#!/usr/bin/env python


"""
Deals with the waveforms
"""


# Python Standard Library
import importlib
import logging

# Other dependencies

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'lvmzxc@gmail.com'


def connect(name, ip, port):
    waveserver = importlib.import_module(f'obspy.clients.{name}')

    logging.info(f'Connecting to {ip}...')
    if name == 'fdsn':
        if ip == 'IRIS':
            client = waveserver.Client(ip)
        else:
            client = waveserver.Client(f'http://{ip}:{port}')
    elif name == 'earthworm':
        client = waveserver.Client(ip, int(port))
    logging.info(f'Succesfully connected to {ip} client.\n')
    return client


if __name__ == '__main__':
    pass
