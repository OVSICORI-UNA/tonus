# tonus

`tonus` is a tool for detection, characterization and cataloguing of seismo-volcanic tonal signals.

# Software installation

`tonus` requieres two different installations:

1. Python for `tonus` software in a *local* computer
2. PostgreSQL for the database in a *remote* or local computer

## Python - local computer

### Anaconda

<!-- TODO: change this -->

You must have Anaconda in your system.  Create a `conda` environment with dependencies:

    $ conda create -n myenv pandas psycopg2 matplotlib=3.3.2
    $ conda activate myenv
    (myenv) $ conda install -c conda-forge obspy
    (myenv) $ conda install numba
    (myenv) $ conda install scikit-image

### tonus

Clone the repository:

    $ git clone https://github.com/OVSICORI-UNA/tonus.git

Install the package in the `conda` environment created previously:

    (myenv) $ cd tonus
    (myenv) $ python setup.py develop

Copy the configuration file:

    cp example/tonus.toml ~/.tonus.toml

## PostgreSQL - remote/local computer

Install PostgreSQL [PostgreSQL](https://www.postgresql.org/download/) wherever your database will reside.
Start the server. You will have to configure PostgreSQL.

# Set-up the database

## Inventory

You will need an station inventory to work with `tonus` at any time.
This inventory will determine the stations that will be available in the database and can be used in the program.
The path to the inventory must be in the configuration file.

If your waveserver can provide it, the inventory can be downloaded from the it.
For example:

```python
import tonus

c = tonus.config.set_conf()

client = tonus.waveserver.connect(**c.waveserver)

inventory = client.get_stations(
    level='response',
    endafter=obspy.UTCDateTime.now(),
    network='OV'
)
inventory.write('path/to/inventory.xml', format='STATIONXML')
```

## Configuration file

First you'll need to modify the following lines of the configuration file:

```toml
inventory = "path/to/inventory"

[db]
host = "localhost"  # IP or "localhost"
user = "user"
password = "password"
database = "tonus"
```

## Run the setup scripts:

1. Create the database by running `tonus-db`.
2. Populate the database with the volcano and stations information:

    tonus-db-populate example/volcanoes.csv

The first step will be executed only once.
On the other hand, you can run step 2 multiple times, in case you need to add
new stations or volcanoes. No duplicate volcanoes or stations will be created.

# Automatic detection

This step could be skipped, if you already detected the events to process.

Default parameters are fined-tuned to detect Turrialba tonal codas. Check the parameters:

    (myenv) $ tonus-detect -h

Run the program:

    (myenv) $ tonus-detect

Use Swarm to check and clean the output.

# Process the detections

    (myenv) $ tonus
