# Demo scripts
Before running this demo script make sure you:

* have running PostgreSQL service,
* have a conda environment with the dependencies as shown in the README file of this repository

## Configuration file

Copy the configuration file example to your root as a hidden dot file:


```bash
cp ./example/tonus.toml ~/.tonus.toml

```
## Activate the conda environment

```bash
conda activate tonus
```

## Create the database

First modify this section of the `toml` file according to your PostgreSQL installation:

```toml
[db]
host = "your host"
user = "your user"
password = "your password"
database = "tonus_test"
```

Then, run the command-line script that 

```bash
tonus-db
```

## Populate the database

First, indicate in the `~/.tonus.toml` file where the inventory is, this will
debpend on where you copied this repository.

```toml
inventory = "[PATH/TO/REPO]/example/inventory.xml"
```

The database will be populated with the information from this inventory.
To do so, run:

```bash
tonus-db-populate ./example/volcanoes.csv
```

## Detect events

First, modify this section of the `~/.tonus.toml` file:

```toml
[detect.io]
input_dir = "[PATH/TO/REPO]/example/wfs/"
output_file = "[PATH/TO/REPO]/example/detect_output.csv"
```

Then, run:

```bash
tonus-detect --starttime 2016-04-25 --endtime 2016-04-26
```

This creates a file `./example/detect_output.csv` in the format of the Swarm software (USGS).
The first column is the start time of the event, the second column is a waveform label, and the third column is the event duration duration.

## Process events

For this demo, we have prepared a command-line script that process the data and inserts it to the database automatically and plots the results.

```bash
python example/automatic_processing.py ./example/detect_output.csv
```
