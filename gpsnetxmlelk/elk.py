#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch


class Elk(Elasticsearch):
    def __init__(self, *args, **kwargs):

        if "index" not in kwargs:
            raise Exception("Please set index!")

        kwargs["timeout"] = 120

        self._index = kwargs["index"]
        del kwargs["index"]

        Elasticsearch.__init__(self, *args, **kwargs)

    def insert(self, doc_type, body):
        return self.index(index=self._index, doc_type=doc_type, body=body)

    def search(self, *args, **kwargs):
        if "index" not in kwargs:
            kwargs["index"] = self._index

        return Elasticsearch.search(self, *args, **kwargs)
