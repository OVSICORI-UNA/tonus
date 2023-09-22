CREATE TABLE volcano (
    id serial NOT NULL,
    volcano varchar NULL UNIQUE,
    latitude float8 NULL,
    longitude float8 NULL,
    CONSTRAINT volcano_pk PRIMARY KEY (id)
);

CREATE TABLE station (
    id serial NOT NULL,
    network varchar NULL,
    station varchar NULL,
    latitude float8 NULL,
    longitude float8 NULL,
    elevation int4 NULL,
    start_date timestamp(0) NULL,
    end_date timestamp(0) NULL,
    volcano_id int4 NULL,
    distance int4 NULL,
    volcano varchar NULL,
    CONSTRAINT station_pk PRIMARY KEY (id),
    CONSTRAINT station_fk FOREIGN KEY (volcano_id) REFERENCES volcano(id) ON DELETE CASCADE
);

CREATE TABLE channel (
    id serial NOT NULL,
    network varchar NULL,
    station varchar NULL,
    location varchar NULL,
    channel varchar NULL,
    volcano varchar NULL,
    sample_rate float8 NULL,
    start_date timestamp(0) NULL,
    end_date timestamp(0) NULL,
    sensor varchar NULL,
    data_logger varchar NULL,
    station_id int4 NULL,
    CONSTRAINT channel_pk PRIMARY KEY (id),
    CONSTRAINT channel_fk FOREIGN KEY (station_id) REFERENCES station(id) ON DELETE CASCADE
);

CREATE TABLE event (
    id serial NOT NULL,
    starttime timestamp(3) NULL,
    endtime timestamp(3) NULL,
    volcano_id int8  NULL,
    CONSTRAINT event_pk PRIMARY KEY (id),
    CONSTRAINT event_fk FOREIGN KEY (volcano_id) REFERENCES volcano(id)
);

CREATE TABLE coda (
    channel_id int8 NOT NULL,
    t1 timestamptz(3) NULL,
    t2 timestamptz(3) NULL,
    t3 timestamptz(3) NULL,
    event_id int8 NOT NULL,
    q_alpha float8 NULL,
    id serial NOT NULL,
    CONSTRAINT coda_pk PRIMARY KEY (id),
    CONSTRAINT coda_un UNIQUE (channel_id, event_id),
    CONSTRAINT coda_times_fk FOREIGN KEY (event_id) REFERENCES "event"(id),
    CONSTRAINT coda_times_fk_1 FOREIGN KEY (channel_id) REFERENCES channel(id)
);

CREATE TABLE coda_peaks (
    frequency float8 NULL,
    amplitude float8 NULL,
    q_f float8 NULL,
    coda_id int8 NULL,
    id serial NOT NULL,
    CONSTRAINT coda_peaks_pk PRIMARY KEY (id),
    CONSTRAINT coda_peaks_fk FOREIGN KEY (coda_id) REFERENCES coda(id)
);

CREATE TABLE tremor (
    id serial NOT NULL,
    event_id int8 NOT NULL,
    channel_id int8 NOT NULL,
    starttime timestamptz(3) NULL,
    endtime timestamptz(3) NULL,
    fmin float8 NULL,
    fmax float8 NULL,
    fmean float8 NULL,
    fstd float8 NULL,
    fmedian float8 NULL,
    n_harmonics int4 NULL,
    amplitude float8 NULL,
    lp_time timestamp(3) NULL,
    lp bool NOT NULL,
    odd bool NULL,
    harmonics _int4 NULL,
    CONSTRAINT harmonic_pk PRIMARY KEY (id),
    CONSTRAINT harmonic_fk FOREIGN KEY (event_id) REFERENCES "event"(id),
    CONSTRAINT harmonic_fk_1 FOREIGN KEY (channel_id) REFERENCES channel(id)
);

CREATE INDEX discrete_id_idx ON event USING btree (id);
