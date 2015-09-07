#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import logging
from tsp import tsp
from datetime import datetime

import webapp2

from google.appengine.api import channel

from jinja2 import Environment, PackageLoader

from odb.sensor import Sensor
from odb.sensor_data import SensorData
from odb.user import User

env = Environment(loader=PackageLoader('frontend', 'templates'))


def jsonify(d):
    return json.dumps(d)


class PostHandler(webapp2.RequestHandler):
    def get(self):
        d = self.request.GET
        logging.info("raw get variables {0}".format(d))
        sensor_id = d["sensor_id"]
        raw = d["value"]
        data = SensorData(sensor_id=sensor_id, raw=raw)
        logging.info("SensorData variables {0}".format(data))
        data.put()

        self.response.write('Saved {0}'.format(data.to_dict()))


class FetchSensorData(webapp2.RequestHandler):
    def get(self):
        d = self.request.GET

        if 'n' in d:
            n = int(d['n'])
        else:
            n = None

        res = SensorData.last_n_by_hours(d["sid"], n)

        # write response
        self.response.content_type = "application/json"
        self.response.write(jsonify([x.json() for x in res]))


class FetchHoursSensorData(webapp2.RequestHandler):
    def get(self):
        d = self.request.GET

        if 'n' in d:
            n = int(d['n'])
        else:
            n = None

        res = SensorData.last_n_by_hours(d["sid"], n, False)

        # write response
        self.response.content_type = "application/json"
        self.response.write(jsonify([x.json() for x in res]))


class FetchGeoJsonList(webapp2.RequestHandler):
    def get(self):
        res = SensorData.all_newest()

        logging.info(res)

        features = [self.geojson(r) for r in res]

        jsn = {
            "type": "FeatureCollection",
            "features": features
        }

        # write response
        self.response.content_type = "application/json"
        self.response.write(jsonify(jsn))

    @staticmethod
    def geojson(r):
        sensor = r.sensor()
        logging.info("r {0}; sensor {1}".format(r, sensor))
        return {
            "type": "Feature",
            "properties": {
                "sensor": sensor.sensor_id,
                "sensor_name": sensor.name,
                "timestamp": datetime.isoformat(r.added, 'T'),
                "color": r.color(),
                "chart_url": "/chart?sensor={0}".format(sensor.sensor_id)
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    float(sensor.wgs84.lon),
                    float(sensor.wgs84.lat)
                ]
            }
        }


class FetchSensorList(webapp2.RequestHandler):
    def get(self):
        res = Sensor.all()

        # write response
        self.response.content_type = "application/json"
        self.response.write(jsonify([x.json() for x in res]))


class RouteUserHandler(webapp2.RequestHandler):
    def post(self):
        # self.response.write('Hello world!')
        req = self.request.params

        minutes_per_day = 1440
        ch_token = channel.create_channel(req["userid"], minutes_per_day)

        u = User(
            userid=req["userid"],
            emails=req["emails"].split(";"),
            ch_token=ch_token,
        )
        u.put()

        logging.info("created new user `{0}`".format(u))

        # write response
        self.response.content_type = "application/json"
        self.response.write(jsonify({
            "ch_token": ch_token,
        }))


class MapViewHandler(webapp2.RequestHandler):
    def get(self):

        if 'loc' not in self.request.GET:
            loc = '58.394146, 15.555303'
        else:
            loc = self.request.GET['loc']
        r, wps = tsp(loc)

        logging.info("r {0}".format(r))

        s = "/".join(r)

        s = "https://www.google.com/maps/dir/" + s

        template = env.get_template('map.html')
        self.response.write(template.render(route_url=s))


class ChartViewHandler(webapp2.RequestHandler):
    def get(self):
        template = env.get_template('chart.html')
        s = Sensor.by_id(self.request.GET['sensor'])
        self.response.write(template.render(sensor=self.request.GET['sensor'], sensor_name=s.name))


class ChartViewHoursHandler(webapp2.RequestHandler):
    def get(self):
        template = env.get_template('chart.html')
        s = Sensor.by_id(self.request.GET['sensor'])
        self.response.write(template.render(sensor=self.request.GET['sensor'], sensor_name=s.name, hours=True))


def timeof(x):
    dt = datetime.strptime(x, '%H:%M')
    return dt.time()


class HoursSetHandler(webapp2.RequestHandler):
    def get(self):
        s = Sensor.by_id(self.request.GET['sensor'])
        s.hours = [timeof(x) for x in self.request.GET['time'].split(',')]
        s.put()
        self.response.write(s)


class RouteHandler(webapp2.RequestHandler):
    def get(self):
        loc = self.request.GET['loc']
        r, wps = tsp(loc)

        logging.info("r {0}".format(r))

        s = "/".join(r)

        s = "https://www.google.com/maps/dir/" + s

        self.response.write('<a href="{0}">{0}</a>'.format(s))


app = webapp2.WSGIApplication(
    [
        ('/post', PostHandler),
        ('/route', RouteHandler),
        ('/sensor', FetchSensorData),  # get all sensor data
        ('/sensor/all', FetchHoursSensorData),  # get all sensor data
        ('/sensor_list', FetchSensorList),  # get list of all sensors
        ('/geojson', FetchGeoJsonList),  # get list of all sensors
        ('/', MapViewHandler),  # map of all sensors
        ('/chart', ChartViewHandler),  # map of all sensors
        ('/chart/hours', ChartViewHoursHandler),  # map of all sensors
        ('/set/hours', HoursSetHandler),  # set hours of a sensor

        ('/router/post', RouteUserHandler),  # send a new message
    ], debug=True
)
