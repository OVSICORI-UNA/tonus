# Python Standard Library
import logging

# Other dependencies
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from obspy.geodetics.base import kilometers2degrees, gps2dist_azimuth

# Local files
from tonus import schema


def create_database(conn, database):
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn:
        c = conn.cursor()
        c.execute(f'CREATE DATABASE {database};')


def get_create_table_sql(table_schema):
    query = f'CREATE TABLE {table_schema.name} (\n'

    query += '\n'.join(
        f'\t{c} {t},' for c, t in table_schema.columns
    )

    for i, constraint in enumerate(table_schema.constraints):
        query += '\n\t' + constraint
        if i != len(table_schema.constraints) - 1:
            query += ','

    query += '\n)'
    query += ';'
    return query


def create_tables(conn):
    table_schemas = [
        schema.volcano,
        schema.station,
        schema.channel,
        schema.event,
        schema.coda,
        schema.coda_peaks,
    ]

    for table_schema in table_schemas:
        with conn:
            c = conn.cursor()
            c.execute(get_create_table_sql(table_schema))

    with conn:
        c = conn.cursor()
        c.execute('CREATE INDEX discrete_id_idx ON event USING btree (id);')


def insert_volcano_stations(
    inventory, volcano, latitude, longitude, maxradius, conn
):
    print('\n', volcano.center(80, '-'))

    query_volcano = f"""
    INSERT INTO volcano
        (volcano, latitude, longitude)
    VALUES
        (%s, %s, %s)
    RETURNING id
    """
    values = (volcano, latitude, longitude)
    with conn:
        cur = conn.cursor()
        cur.execute(query_volcano, values)
        volcano_id = cur.fetchone()[0]

    try:
        _inventory = inventory.select(
            latitude=latitude, longitude=longitude,
            maxradius=kilometers2degrees(maxradius)
        )
    except Exception as e:
        logging.warning(e)
        logging.warning(
            f'No stations within {maxradius} km of {volcano} volcano.'
        )
        return

    station_columns = [c[0] for c in schema.station.columns if c[0] != 'id']
    values_fmt      = ', '.join('%s' for c in station_columns)

    query_station = f"""
    INSERT INTO
        station ({', '.join(station_columns)})
    VALUES
        ({values_fmt})
    RETURNING
        id
    """

    channel_columns = [c[0] for c in schema.channel.columns if c[0] != 'id']
    values_fmt      = ', '.join('%s' for c in channel_columns)

    query_channel = f"""
    INSERT INTO
        channel ({', '.join(channel_columns)})
    VALUES
        ({values_fmt});
    """

    for network in _inventory:
        for station in network:
            print(station.code)
            distance = int(gps2dist_azimuth(
                latitude, longitude, station.latitude, station.longitude
            )[0])

            if station.end_date is None:
                end_date = None
            else:
                end_date = station.end_date.datetime

            values = [
                network.code, station.code, station.latitude,
                station.longitude, station.elevation,
                station.start_date.datetime, end_date, volcano_id, distance,
                volcano
            ]

            try:
                with conn:
                    cur = conn.cursor()
                    cur.execute(query_station, values)
                    station_id = cur.fetchone()[0]
            except Exception as e:
                logging.warning(e)
                continue

            for channel in station:

                if channel.end_date is None:
                    end_date = None
                else:
                    end_date = channel.end_date.datetime

                if channel.sensor is None:
                    sensor = None
                else:
                    sensor = channel.sensor.description

                if channel.data_logger is None:
                    data_logger = None
                else:
                    data_logger = channel.data_logger.description

                values = [
                    network.code,
                    station.code,
                    channel.location_code,
                    channel.code,
                    volcano,
                    channel.sample_rate,
                    channel.start_date.datetime,
                    end_date,
                    sensor,
                    data_logger,
                    station_id
                ]

                with conn:
                    cur = conn.cursor()
                    cur.execute(query_channel, values)
    return
