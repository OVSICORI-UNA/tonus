# Python Standard Library

# Other dependencies
import pandas as pd

# Local files

def get_volcanoes_with_event(event_type, conn):
    query = f"""
    WITH
        volcano_ids
    AS (
        SELECT DISTINCT
            volcano_id
        FROM
            event
        WHERE EXISTS (
            SELECT 1 FROM
                {event_type}
            WHERE
                {event_type}.event_id = event.id LIMIT 1
        )
    )
    SELECT
        volcano
    FROM
        volcano
    WHERE
        id
    IN (
        SELECT
            volcano_id
        FROM
        volcano_ids
    );
    """

    return pd.read_sql_query(query, conn).volcano.tolist()


def get_stacha_with_event(volcano, event_type, conn):
    query = f"""
    SELECT
        channel.station, channel.channel, channel.id
    FROM
        channel

    INNER JOIN
        station
    ON
        channel.station_id = station.id

    INNER JOIN
        volcano
    ON
        station.volcano_id = volcano.id
    WHERE
        volcano.volcano = '{volcano}'
    AND EXISTS (
        SELECT 1 FROM
            {event_type}
        WHERE
        {event_type}.channel_id = channel.id LIMIT 1
    );
    """
    df = pd.read_sql_query(query, conn)
    return df.station.tolist(), df.channel.tolist(), df.id.tolist()


def _get_coda_data(channel_ids, conn):
    query = f"""
    SELECT
        coda.t1, coda.t2, coda.t3,
        coda.channel_id, coda.event_id,
        coda_peaks.frequency, coda_peaks.q_f,
        coda_peaks.amplitude,
        channel.station, channel.channel
    FROM
        coda_peaks

    INNER JOIN
        coda
    ON
        coda_peaks.coda_id = coda.id

    INNER JOIN
        channel
    ON
        coda.channel_id = channel.id

    WHERE
        coda.channel_id IN ({','.join(channel_ids)});
    """

    df = pd.read_sql_query(query, conn)

    # for t in 't1 t2 t3'.split():
        # df[t] = df[t].dt.tz_convert('America/Guatemala')

    query = f"""
    SELECT
        event.starttime, event.id, coda.channel_id
    FROM
        event

    INNER JOIN
        coda
    ON
        coda.event_id = event.id

    INNER JOIN
        channel
    ON
        coda.channel_id = channel.id

    WHERE
        coda.channel_id IN ({','.join(channel_ids)});
    """
    hist = pd.read_sql_query(query, conn)
    return df, hist


def _get_tremor_data(channel_ids, conn):
    query = f"""
    SELECT
        tremor.starttime, tremor.endtime, tremor.lp,
        tremor.fmean, tremor.fmin, tremor.fmax,
        tremor.n_harmonics, tremor.amplitude,
        tremor.channel_id,
        channel.station, channel.channel
    FROM
        tremor

    INNER JOIN
        channel
    ON
        tremor.channel_id = channel.id

    WHERE
        tremor.channel_id IN ({','.join(channel_ids)});
    """

    df = pd.read_sql_query(query, conn)

    # for t in 'starttime endtime'.split():
    #     df[t] = df[t].dt.tz_convert('America/Guatemala')

    query = f"""
    SELECT
        event.starttime, event.id, tremor.channel_id
    FROM
        event

    INNER JOIN
        tremor
    ON
        tremor.event_id = event.id

    INNER JOIN
        channel
    ON
        tremor.channel_id = channel.id

    WHERE
        tremor.channel_id IN ({','.join(channel_ids)});
    """
    hist = pd.read_sql_query(query, conn)
    return df, hist


def get_data(channel_ids, event_type, conn):
    if event_type == 'coda':
        df, hist = _get_coda_data(channel_ids, conn)
    elif event_type == 'tremor':
        df, hist = _get_tremor_data(channel_ids, conn)

    df['stacha'] = df.station+' '+df.channel+' '+df.channel_id.apply(str)
    return df, hist
