#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name="gpsnetxmlelk",
      version="1.0.0",
      author="Krzysztof Otręba",
      author_email="krzotr@gmail.com",
      download_url="https://github.com/krzotr/gpsnetxmlelk",
      url="https://github.com/krzotr/gpsnetxmlelk",
      install_requires=["elasticsearch", "gpsnetxml"],
      dependency_links=[
          "http://github.com/krzotr/gpsnetxml/tarball/dev#egg=gpsnetxml"
      ],
      long_description="""Insert .gpsxml and .netxml into Elasticsearch""",
      packages=["gpsnetxmlelk"],
      scripts=['bin/gpsnetxml2elk'],
      package_data={"gpsnetxmlelk": ["asset/*"]},
      classifiers=["Programming Language :: Python",
                   "Topic :: Internet :: Log Analysis",
                   "Topic :: System :: Networking",
                   "Topic :: Utilities"],
      keywords="kismet gpsxml netxml gpsnetxml wifi wpa wpa2 wep elasticsearch")
