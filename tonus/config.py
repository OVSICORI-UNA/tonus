#!/usr/bin/env python


"""
This modules handles the configuration file.
"""


# Python Standard Library
import os
import tomllib

# Other dependencies

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'laat@umich.edu'


CONF_FILEPATH = os.path.join(os.path.expanduser('~'), '.tonus.toml')


class Conf(dict):
    def __init__(self, *args, **kwargs):
        super(Conf, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    if isinstance(v, dict):
                        v = Conf(v)
                    if isinstance(v, list):
                        self.__convert(v)
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                if isinstance(v, dict):
                    v = Conf(v)
                elif isinstance(v, list):
                    self.__convert(v)
                self[k] = v

    def __convert(self, v):
        for elem in range(0, len(v)):
            if isinstance(v[elem], dict):
                v[elem] = Conf(v[elem])
            elif isinstance(v[elem], list):
                self.__convert(v[elem])

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Conf, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Conf, self).__delitem__(key)
        del self.__dict__[key]


def set_conf(filepath=None):
    if filepath is None:
        filepath = CONF_FILEPATH
    with open(filepath, 'rb') as f:
        c = Conf(tomllib.load(f))
    return c


if __name__ == '__main__':
    pass
