#!/bin/sh

curl -XDELETE http://127.0.0.1:9200/kisme

echo

curl -XPUT http://127.0.0.1:9200/kisme -d @structure.json

echo


# Speed up inserting data
curl -XPUT http://127.0.0.1:9200/kisme/_settings -d '{
    "index": {
            "refresh_interval" : "60s",
            "translog.flush_threshold_ops": 50000
    }
}'

echo
