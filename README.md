# Installation

1. Create a `conda` environment with dependencies:  `obspy`, `pandas` and `psycopg2`

    ```
    $ conda create -n tonus pandas psycopg2 matplotlib=3.3.2
    $ conda activate tonus
    (tonus) $ conda install -c conda-forge obspy
    ```

2. Clone the repository:

    ```
    $ git clone https://github.com/OVSICORI-UNA/tonus.git
    ```

3. Install the package in the `conda` environment created in step 1:

    ```
    (env) $ cd tonus
    (env) $ pip install -e .
    ```

4. Create your configuration file `~/.tonus.json`, by copying *and* modifying the following:
    ```
    {
        "fdsn": {
            "ip": "",
            "port": ""
        },
        "db": {
            "host": "",
            "user": "",
            "password": "",
            "database": ""
        },
        "network": "OV,TC",
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
        }
    }
    ```

# Run the program

Run the program:

    ```
    $ conda activate tonus
    (tonus) $ tonus
    ```
