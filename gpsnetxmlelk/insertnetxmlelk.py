#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gpsnetxml import ParseNetxml


class Netxml2Elk(object):
    """
    Prepare netxml file to elasticsearch

    - rename first_time to time in ssid, networks, clients
    - add location field in networks and clients
    - rename packets to packets_no in seen_cards and ssids
    - add bssid to clients
    - add bssid and client_mac to seen_cards
    """

    def __init__(self, file):
        self._file = file

    def _fix_ssids(self, net, bssid, client_mac=None):
        ssids = net["ssids"]

        i = 0
        for ssid in ssids:
            ssids[i]["bssid"] = bssid

            ssids[i]["time"] = ssids[i]["first_time"]
            del ssids[i]["first_time"]

            if client_mac:
                ssids[i]["client_mac"] = client_mac
                ssids[i]["packets_no"] = ssids[i]["packets"]

                del ssids[i]["packets"]

            i += 1

        net["ssids"] = ssids

    def _fix_cards(self, net, bssid, client_mac=None):
        cards = []

        for uuid, card in net["seen_cards"].items():
            c = card
            c.update({
                "bssid": bssid,
                "uuid": uuid,
                "packets_no": c["packets"]
            })

            del c["packets"]

            if client_mac:
                c["client_mac"] = client_mac

            cards.append(c)

        net["seen_cards"] = cards

    def _fix_gps(self, net):
        # Ignore AVG, because contains invalid data like -88.981823, -124.525371
        # or alt -143091.076600
        net["location"] = {
            "min": {
                "lat": net["gps_info"]["min_lat"],
                "lon": net["gps_info"]["min_lon"]
            },
            "max": {
                "lat": net["gps_info"]["max_lat"],
                "lon": net["gps_info"]["max_lon"]
            },
            "peak": {
                "lat": net["gps_info"]["peak_lat"],
                "lon": net["gps_info"]["peak_lon"]
            }
        }

    def _fix_network(self, net, bssid):
        self._fix_ssids(net, bssid)
        self._fix_cards(net, bssid)
        self._fix_gps(net)

        net["time"] = net["first_time"]
        del net["first_time"]

    def _fix_clients(self, net, bssid):
        if not net["wireless_clients"]:
            return []

        clients = net["wireless_clients"]

        i = 0
        for client in clients:
            clients[i]["bssid"] = bssid
            clients[i]["time"] = clients[i]["first_time"]
            del clients[i]["first_time"]

            client_mac = client["client_mac"]

            print("    " + client_mac)

            self._fix_ssids(clients[i], bssid, client_mac)
            self._fix_cards(clients[i], bssid, client_mac)
            self._fix_gps(clients[i])

            i += 1

        net["wireless_clients"] = clients

    def get_network(self):
        netxml = ParseNetxml(self._file, "%Y-%m-%dT%H:%M:%S.0")

        for net in netxml.get_networks():
            bssid = net["bssid"]

            self._fix_network(net, bssid)
            self._fix_clients(net, bssid)

            yield net


class InsertNetxmlElk(object):
    """
    Insert netxml data to elasticsearch

    Insert clients/seen_cards
    Insert clients/ssids
    Insert clients
    Insert networks/ssids
    Insert networks/clients
    Insert networks/seen_cards

    """

    def __init__(self, elk, file, file_id):
        self._file = file
        self._index = "kisme"
        self._file_id = file_id

        self._elk = elk

    def _insert_cards(self, n):
        ret = []
        for c in n["seen_cards"]:
            try:
                out = self._elk.insert("seen_cards", c)
                ret.append(out["_id"])
            except Exception as e:
                print("seen_cards error :(; " + str(e))

        return ret

    def _insert_ssids(self, n):
        ret = []

        for s in n["ssids"]:
            try:
                out = self._elk.insert("ssids", s)
                ret.append(out["_id"])
            except Exception as e:
                print("ssids error :(; " + str(e))

        return ret

    def _insert_clients(self, n):
        if not n["wireless_clients"]:
            return []

        ret = []

        for c in n["wireless_clients"]:
            try:
                c["ssids"] = self._insert_ssids(c)
                c["seen_cards"] = self._insert_cards(c)
                c["files"] = self._file_id

                out = self._elk.insert("wireless_clients", c)

                ret.append(out["_id"])
            except Exception as e:
                print("wireless_clients error :(; " + str(e))

        return ret

    def insert(self):
        net = Netxml2Elk(self._file)

        for n in net.get_network():
            n["ssids"] = self._insert_ssids(n)
            n["seen_cards"] = self._insert_cards(n)
            n["wireless_clients"] = self._insert_clients(n)
            n["files"] = self._file_id

            print(n["bssid"])

            try:
                self._elk.insert("networks", n)
            except Exception as e:
                print("network :(; " + str(e))
