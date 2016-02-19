#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import sys

from collections import OrderedDict
from elk import *


class Elk2kismon(object):
    """
    Export networks from Elasticsearch to networks.json Kismon format
    """

    def __init__(self, output, dbg=False):
        self._output = output
        self._dbg = dbg
        self._networks = {}

        self._elk = Elk(index="kisme")

    def _debug(self, msg):
        if not self._dbg:
            return

        print(msg, file=sys.stderr)

    def _get_crypt_list(self):
        """
        From Kismon source code
        """

        cryptsets = ["none", "unknown", "wep", "layer3 ", "wep40", "wep104",
                     "tkip", "wpa", "psk", "aes_ocb", "aes_ccm", "leap", "ttls",
                     "peap", "pptp", "fortress", "keyguard"]

        return cryptsets

    def _encode_cryptset(self, crypts):
        """
        From Kismon source code
        """

        for crypt in crypts:
            if crypt.startswith("wpa+"):
                crypts.append(crypt.split("+")[1].lower().replace("-", "_"))

        cryptsets = self._get_crypt_list()
        bin_cryptset = []

        for crypt in cryptsets:
            if crypt in crypts:
                bit = "1"
            else:
                bit = "0"
            bin_cryptset.insert(0, bit)

        cryptset = int("".join(bin_cryptset[:-1]), 2)

        return cryptset

    def _get_encryptions(self, bssid):
        """
        Get all encryptions from Elasticsearch
        """

        body = {
            "query": {
                "filtered": {
                    "query": {
                        "query_string": {
                            "analyze_wildcard": True,
                            "query": "_type:ssids +bssid:\"%s\"" % (bssid, )
                        }
                    },
                    "filter": {
                        "bool": {
                            "must": [{
                                "query": {
                                    "query_string": {
                                        "analyze_wildcard": True,
                                        "query": "*"
                                    }
                                }
                            }]
                        }
                    }
                }
            },
            "size": 0,
            "aggs": {
                "2": {
                    "terms": {
                        "field": "encryption",
                        "size": 15,
                        "order": {
                            "_count": "desc"
                        }
                    }
                }
            }
        }

        try:
            encryptions = self._elk.search(doc_type="ssids", body=body)

            enc = []

            for e in encryptions["aggregations"]["2"]["buckets"]:
                enc.append(str(e["key"].lower().replace("-", "_")))

            return self._encode_cryptset(enc)
        except:
            pass

        return 0

    def _get_essid(self, bssid):
        """
        Get most popular essid from Elasticsearch
        """

        body = {
            "query": {
                "filtered": {
                    "query": {
                        "query_string": {
                            "analyze_wildcard": True,
                            "query": "_type:ssids +bssid:\"%s\"" % (bssid, )
                        }
                    },
                    "filter": {
                        "bool": {
                            "must": [{
                                "query": {
                                    "query_string": {
                                        "analyze_wildcard": True,
                                        "query": "*"
                                    }
                                }
                            }]
                        }
                    }
                }
            },
            "size": 0,
            "aggs": {
                "2": {
                    "terms": {
                        "field": "essid",
                        "size": 1,
                        "order": {
                            "_count": "desc"
                        }
                    }
                }
            }
        }

        try:
            essid = self._elk.search(doc_type="ssids", body=body)

            return essid["aggregations"]["2"]["buckets"][0]["key"]
        except:
            pass

        return ""

    def _get_network_info(self, bssid):
        """
        Get lat lon, manuf, network type, cryptset and essid from Elasticsearch.
        """

        q = "+bssid:\"%s\" +snr_info.max_signal_dbm:[-120 TO -10] -gps_info.peak_lat:0 -gps_info.peak_lon:0" % (bssid,)

        try:
            try:
                # Ignore lat/lon 0.0 and incorrect signal
                net = self._elk.search(doc_type="networks", size=1,
                                       sort="snr_info.max_signal_dbm:asc,"
                                            "gps_info.peak_lon:desc",
                                       q=q)
            except:
                net = self._elk.search(doc_type="networks", size=1,
                                       sort="snr_info.max_signal_dbm:asc,"
                                            "gps_info.peak_lon:desc",
                                       q="+bssid:\"%s\"" % (bssid,))

            net = net["hits"]["hits"][0]["_source"]

            network = {
                "lat": float(net["gps_info"]["peak_lat"]),
                "lon": float(net["gps_info"]["peak_lon"]),
                "manuf": net["manuf"],
                "type": net["type"],
                "cryptset": self._get_encryptions(bssid),
                "ssid": self._get_essid(bssid),
            }

            return network
        except:
            pass

        return {
            "lat": .0,
            "lon": .0,
            "manuf": "",
            "type": "unknown",
            "cryptset": 0,
            "ssid": "",
        }

    def _get_networks_from_elk(self):
        """
        Get all networks from Elasticsearch
        """

        body = {
            "query": {
                "filtered": {
                    "query": {
                        "query_string": {
                            "analyze_wildcard": True,
                            "query": "+type:networks +snr_info.min_signal_dbm:[-120 TO -10] +snr_info.max_signal_dbm:[-120 TO -10] +snr_info.last_signal_dbm:[-120 TO -10]"
                        }
                    },
                    "filter": {
                        "bool": {
                            "must": [{
                                "query": {
                                    "query_string": {
                                        "analyze_wildcard": True,
                                        "query": "*"
                                    }
                                }
                            }, {
                                "range": {
                                    "time": {
                                        "gte": 0,
                                        "lte": 1455921849324
                                    }
                                }
                            }]
                        }
                    }
                }
            },
            "size": 0,
            "aggs": {
                "statistics": {
                    "terms": {
                        "field": "bssid",
                        "size": 0,
                        "order": {
                            "_count": "desc"
                        }
                    },
                    "aggs": {
                        "1": {
                            "cardinality": {
                                "field": "bssid"
                            }
                        },
                        "12": {
                            "min": {
                                "field": "time"
                            }
                        },
                        "13": {
                            "max": {
                                "field": "time"
                            }
                        },
                        "14": {
                            "avg": {
                                "field": "channel"
                            }
                        },
                        "15": {
                            "min": {
                                "field": "snr_info.min_signal_dbm"
                            }
                        },
                        "16": {
                            "max": {
                                "field": "snr_info.max_signal_dbm"
                            }
                        }
                    }
                }
            }
        }

        self._debug("Downloading networks from Elasticsearch ...")

        data = self._elk.search(doc_type="networks", body=body)

        self._debug("Downloaded %d networks" % (
            len(data["aggregations"]["statistics"]["buckets"])))

        for n in data["aggregations"]["statistics"]["buckets"]:
            bssid = n["key"]

            self._networks[bssid] = OrderedDict((
                ("channel", int(n["14"]["value"])),
                ("cryptset", 0),
                ("firsttime", int(n["12"]["value"]/1000)),
                ("lasttime", int(n["13"]["value"]/1000)),
                ("lat", .0),
                ("lon", .0),
                ("manuf", ""),
                ("signal_dbm", OrderedDict((
                    ("last", int(n["16"]["value"])),
                    ("max", int(n["15"]["value"])),
                    ("min", int(n["16"]["value"])),
                ))),
                ("ssid", 0),
                ("type", ""),
                ("comment", "")
            ))

        # After aggregation we don't have essid, best lat/lon, encryption manuf
        # and network type. We need download additional informations from
        # Elasticsearch
        remove = []

        self._debug("Downloading networks details from Elasticsearch ...")

        i = 0
        for bssid in self._networks:
            n = self._networks[bssid]

            net = self._get_network_info(bssid)

            if not net:
                self.debug("Cannot download informations about %s" % (bssid,))
                remove.append(bssid)
            else:
                n.update(net)

            if i and i % 100 == 0:
                self._debug("%d / %d networks" % (i, len(self._networks)))

            i += 1

        for r in remove:
            del self._networks[r]

    def get_networks():
        """
        Return list of all networks
        """

        if len(self._networks) == 0:
            self._get_networks_from_elk()

        return self._networks

    def save(self):
        """
        Write networks to file
        """

        self._get_networks_from_elk()

        f = open(self._output, "w")
        f.write(json.dumps(self._networks, indent=4))
        f.close()
