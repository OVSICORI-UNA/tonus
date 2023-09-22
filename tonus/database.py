#!/usr/bin/env python


"""
"""


# Python Standard Library
import logging

# Other dependencies
from obspy.geodetics.base import kilometers2degrees, gps2dist_azimuth

# Local files


__author__ = 'Leonardo van der Laat'
__email__ = 'laat@umich.edu'


def get_column_names(table_name, conn):
    query = f"""
    SELECT
        column_name
    FROM
        information_schema.columns
    WHERE
        table_name = '{table_name}'
    AND
        column_name != 'id';
    """
    cursor = conn.cursor()
    cursor.execute(query)
    return [row[0] for row in cursor]


def insert_volcano_stations(
    inventory, volcano, latitude, longitude, maxradius, conn
):
    print('\n', volcano.center(80, '-'))

    query_volcano = """
    INSERT INTO volcano
        (volcano, latitude, longitude)
    VALUES
        (%s, %s, %s)
    RETURNING id
    """
    values = (volcano, latitude, longitude)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(query_volcano, values)
    except Exception as e:
        print(e)
        _query = f"SELECT id FROM volcano WHERE volcano = '{volcano}';"

        with conn:
            cur = conn.cursor()
            cur.execute(_query)
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

    station_columns = get_column_names('station', conn)
    values_fmt = ', '.join('%s' for c in station_columns)

    query_station = f"""
    INSERT INTO
        station ({', '.join(station_columns)})
    VALUES
        ({values_fmt})
    RETURNING
        id
    """

    channel_columns = get_column_names('channel', conn)
    values_fmt = ', '.join('%s' for c in channel_columns)

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


def remove_duplicates(conn):
    query = """
    DELETE FROM station
    WHERE id IN (
            SELECT id FROM station
            EXCEPT SELECT MIN(id) FROM station
            GROUP BY station, latitude, longitude
    );
    """
    with conn:
        c = conn.cursor()
        c.execute(query)
    return


if __name__ == '__main__':
    pass
