from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name             = 'tonus',
    version          = '0.1',
    description      = 'Extract tornillo-type event information',
    long_description =  readme(),
    url              = 'https://github.com/OVSICORI-UNA/tonus',
    author           = 'Leonardo van der Laat',
    author_email     = 'leonardo.vanderlaat.munoz@una.cr',
    packages         = ['tonus'],
    install_requires = [
    ],
    scripts          = [
        'bin/tonus',
    ],
    zip_safe         = False
)
