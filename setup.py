#!/usr/bin/env python


"""
"""


from setuptools import setup


__author__ = 'Leonardo van der Laat'
__email__ = 'laat@umich.edu'


def main():
    return


def readme():
    with open('README.md') as f:
        return f.read()


if __name__ == '__main__':
    setup(
        name='tonus',
        version='0.1',
        description='Analysis tonal seismo-volcanic signals',
        long_description=readme(),
        url='https://github.com/OVSICORI-UNA/tonus',
        author='Leonardo van der Laat',
        author_email='laat@umich.edu',
        packages=['tonus'],
        install_requires=[],
        scripts=[
            'bin/tonus',
            'bin/tonus-db',
            'bin/tonus-db-populate',
            'bin/tonus-detect',
        ],
        zip_safe=False
    )
