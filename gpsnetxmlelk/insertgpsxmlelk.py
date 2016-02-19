#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from gpsnetxml import ParseGpsxml


class InsertGpsxmlElk(object):
    def __init__(self, elk, file, file_id):
        self._file = file
        self._index = "kisme"
        self._file_id = file_id

        self._elk = elk

    def insert(self):
        gps = ParseGpsxml(self._file)

        time_format = "%Y-%m-%dT%H:%M:%S"

        for g in gps.get_points():
            ts = time.strftime(time_format, time.localtime(g["time_sec"]))

            g["time"] = "%s.%d" % (ts, g["time_usec"] // 1000)
            g["location"] = {
                "lat": g["lat"],
                "lon": g["lon"]
            }
            g["files"] = self._file_id

            del g["lat"], g["lon"], g["time_sec"], g["time_usec"]

            try:
                self._elk.insert("gps", g)
                print(g["bssid"])
            except:
                print("gpspoint error :(")
