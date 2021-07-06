# Installation

1. Create a `conda` environment with dependencies:

    ```
    $ conda create -n myenv pandas psycopg2 matplotlib=3.3.2
    $ conda activate myenv
    (myenv) $ conda install -c conda-forge obspy
    (myenv) $ conda install numba
    (myenv) $ conda install scikit-image
    ```

2. Clone the repository:

    ```
    $ git clone https://github.com/OVSICORI-UNA/tonus.git
    ```

3. Install the package in the `conda` environment created in step 1:

    ```
    (myenv) $ cd tonus
    (myenv) $ pip install -e .
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
        "network": "NN,NN",
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

# Automatic detection

This step could be skipped, if you already detected the events to process.

Default parameters are fined-tuned to detect Turrialba tonal codas. Check the parameters:

    (myenv) $ tonus-detect -h

Run the program:

    (myenv) $ tonus-detect

Use Swarm to check and clean the output.

# Process the detections

    (myenv) $ tonus
