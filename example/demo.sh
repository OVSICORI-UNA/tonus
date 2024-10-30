conda activate tonus

tonus-db
# TODO borrar el path
tonus-db-populate ./example/volcanoes.csv
tonus-detect --starttime 2016-04-25 --endtime 2016-04-26
