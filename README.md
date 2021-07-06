# Installation

## Python

### Anaconda

You must have Anaconda in your system.  Create a `conda` environment with dependencies:

    ```
    $ conda create -n myenv pandas psycopg2 matplotlib=3.3.2
    $ conda activate myenv
    (myenv) $ conda install -c conda-forge obspy
    (myenv) $ conda install numba
    (myenv) $ conda install scikit-image
    ```

### tonus

Clone the repository:

    ```
    $ git clone https://github.com/OVSICORI-UNA/tonus.git
    ```

Install the package in the `conda` environment created previously:

    ```
    (myenv) $ cd tonus
    (myenv) $ pip install -e .
    ```

## PostgreSQL

Install PostgreSQL [PostgreSQL](https://www.postgresql.org/download/linux/ubuntu/) wherever your database will reside.


# Configuration file

Create your configuration file `~/.tonus.json`, by copying *and* modifying the following:
    ```
    {
        "fdsn": {
            "ip": "",
            "port": ""
        },
        "inventory": "/Users/leo/.tonus_inventory.xml", 
        "db": {
            "host": "",
            "user": "",
            "password": "",
            "database": ""
        },
        "network": "NN,NN",
        "max_radius": 4,
        "swarm_dir": "/path/to/swarm.csv",
        "duration": 40,
        "spectrogram": {
            "nfft": 256,
            "mult": 8,
            "per_lap": 0.9,
            "ymin": 0.1,
            "ymax": 30,
            "dbscale": true,
            "cmap": "rainbow",
            "std_factor": 4
        },
        "process": {
            "freqmin": 1,
            "freqmax": 15,
            "order": 4,
            "factor": 4
            "distance_Hz": 0.75
        }
    }
    ```

# Set the database
## Define your volcanoes

Create a `csv` like the following example, let's call it `volcanoes.csv`:

    | volcano            | latitude | longitude |
    |--------------------|----------|-----------|
    | Rincón de la Vieja |   10.831 |   -85.336 |

## Create the database

    (myenv) $ tonus-db volcanoes.csv

## Clean the database

Use your database manager (e.g. DBeaver) to:
* Remove repeated stations (older stations or repeating in near but different volcanoes):
    * find out the `id` of the volcano,
    * filter the `station` table with `volcano_id = {id}`
    * Remove the row

# Automatic detection

This step could be skipped, if you already detected the events to process.

Default parameters are fined-tuned to detect Turrialba tonal codas. Check the parameters:

    (myenv) $ tonus-detect -h

Run the program:

    (myenv) $ tonus-detect

Use Swarm to check and clean the output.

# Process the detections

    (myenv) $ tonus
