# Python Standard Library
from collections import namedtuple

# Other dependencies

# Local files


TableSchema = namedtuple(
    'Schema', ['name', 'columns', 'constraints']
)

volcano = TableSchema(
    'volcano',
    [
        ('id', 'serial NOT NULL'),
        ('volcano', 'varchar NULL UNIQUE'),
        ('latitude', 'float8 NULL'),
        ('longitude', 'float8 NULL'),
    ],
    ['CONSTRAINT volcano_pk PRIMARY KEY (id)']
)

station = TableSchema(
    'station',
    [
        ('id', 'serial NOT NULL'),
        ('network', 'varchar NULL'),
        ('station', 'varchar NULL'),
        ('latitude', 'float8 NULL'),
        ('longitude', 'float8 NULL'),
        ('elevation', 'int4 NULL'),
        ('start_date', 'timestamp(0) NULL'),
        ('end_date', 'timestamp(0) NULL'),
        ('volcano_id', 'int4 NULL'),
        ('distance', 'int4 NULL'),
        ('volcano', 'varchar NULL')
    ],
    [
        'CONSTRAINT station_pk PRIMARY KEY (id)',
        'CONSTRAINT station_fk FOREIGN KEY (volcano_id) REFERENCES volcano(id) ON DELETE CASCADE'
    ]
)

channel = TableSchema(
    'channel',
    [
        ('id', 'serial NOT NULL'),
        ('network', 'varchar NULL'),
        ('station', 'varchar NULL'),
        ('location', 'varchar NULL'),
        ('channel', 'varchar NULL'),
        ('volcano', 'varchar NULL'),
        ('sample_rate', 'float8 NULL'),
        ('start_date', 'timestamp(0) NULL'),
        ('end_date', 'timestamp(0) NULL'),
        ('sensor', 'varchar NULL'),
        ('data_logger', 'varchar NULL'),
        ('station_id', 'int4 NULL')
    ],
    [
        'CONSTRAINT channel_pk PRIMARY KEY (id)',
        'CONSTRAINT channel_fk FOREIGN KEY (station_id) REFERENCES station(id) ON DELETE CASCADE'
    ]
)

event = TableSchema(
    'event',
    [
        ('id', 'serial NOT NULL'),
        ('starttime', 'timestamp(3) NULL'),
        ('endtime', 'timestamp(3) NULL'),
        ('volcano_id', 'int8  NULL'),
    ],
    [
        'CONSTRAINT event_pk PRIMARY KEY (id)',
        'CONSTRAINT event_fk FOREIGN KEY (volcano_id) REFERENCES volcano(id)'
    ]
)

tornillo = TableSchema(
    'tornillo',
    [
	('channel_id', 'int8 NOT NULL'),
	('t1', 'timestamptz(3) NULL'),
	('t2', 'timestamptz(3) NULL'),
	('t3', 'timestamptz(3) NULL'),
	('event_id', 'int8 NOT NULL'),
	('q_alpha', 'float8 NULL'),
	('id', 'serial NOT NULL'),
    ],
    [
	'CONSTRAINT tornillo_pk PRIMARY KEY (id)',
	'CONSTRAINT tornillo_un UNIQUE (channel_id, event_id)',
	'CONSTRAINT tornillo_times_fk FOREIGN KEY (event_id) REFERENCES "event"(id)',
	'CONSTRAINT tornillo_times_fk_1 FOREIGN KEY (channel_id) REFERENCES channel(id)'
    ]
)

tornillo_peaks = TableSchema(
    'tornillo_peaks',
    [
	('frequency', 'float8 NULL'),
	('amplitude', 'float8 NULL'),
	('q_f', 'float8 NULL'),
	('tornillo_id', 'int8 NULL'),
	('id', 'serial NOT NULL'),
    ],
    [
        'CONSTRAINT tornillo_peaks_pk PRIMARY KEY (id)',
	'CONSTRAINT tornillo_peaks_fk FOREIGN KEY (tornillo_id) REFERENCES tornillo(id)'
    ]
)
