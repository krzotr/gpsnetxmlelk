#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

from gpsnetxml import ParseGpsxml
from gpsnetxml import ParseNetxml
from . elk import Elk
from . insertnetxmlelk import InsertNetxmlElk
from . insertgpsxmlelk import InsertGpsxmlElk


class InsertGpsnetxmlElk(object):
    """
    Insert .gpsxml and .netxml into Elasticsearch. Skip currently added files
    """

    def __init__(self, files, index="kismet"):
        self._files = []
        f = []

        for file in files:
            if file[-7:] == ".gpsxml":
                f.append(file[:-7])
            elif file[-7:] == ".netxml":
                f.append(file[:-7])
            else:
                f.append(file)

        f = list(set(f))

        for file in f:
            if (os.path.isfile(file + ".gpsxml")
                and os.path.isfile(file + ".netxml")):
                self._files.append(file)

        if self._files == []:
            raise Exception("Please set correct file or files")

        self._elk = Elk(index=index)

    def insert(self):
        print(json.dumps(self._files, indent=4))

        for file in self._files:
            gpsxml = file + ".gpsxml"
            netxml = file + ".netxml"

            meta = {}

            gps = ParseGpsxml(file=gpsxml, date_format="%Y-%m-%dT%H:%M:%S.0")
            meta.update(gps.get_metadata())

            elk_meta = self._elk.search(doc_type="files", size=1,
                                        q="file:\"%s\"" % (meta["file"],))

            if elk_meta["hits"]["total"] > 0:
                print("File %s exists in elasticsearch!" % (netxml,))
                continue

            try:
                net = ParseNetxml(file=netxml,
                                  date_format="%Y-%m-%dT%H:%M:%S.0")
                meta.update(net.get_metadata())

                meta["time"] = meta["start_time"]
                del meta["start_time"]

                file_id = self._elk.insert("files", meta)["_id"]

                print("Inserting networks to database from " + netxml)
                net = InsertNetxmlElk(self._elk, netxml, file_id)
                net.insert()

                print("Inserting gpspoints to database from " + gpsxml)
                gps = InsertGpsxmlElk(self._elk, gpsxml, file_id)
                gps.insert()
            except Exception as e:
                print("Error :( " + str(e))
