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
        sensor_id = d["sensor_id"]
        raw = d["value"]
        data = SensorData(sensor_id=sensor_id, raw=raw)
        data.put()

        self.response.write('Saved {0}'.format(data.to_dict()))


class FetchSensorData(webapp2.RequestHandler):
    def get(self):
        d = self.request.GET

        if 'n' in d:
            n = int(d['n'])
        else:
            n = None

        res = SensorData.last_n(d["sid"], n)

        # write response
        self.response.content_type = "application/json"
        self.response.write(jsonify([x.json() for x in res]))


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


class RegistrationHandler(webapp2.RequestHandler):
    def get(self):
        if "userid" not in self.request.GET:
            self.response.write("missing userid get variable")
            return
        userid = self.request.GET["userid"]

        template = env.get_template('register.html')
        self.response.write(template.render(userid=userid))


app = webapp2.WSGIApplication(
    [
        ('/post', PostHandler),
        ('/sensor', FetchSensorData),  # get all sensor data
        ('/sensor_list', FetchSensorList),  # get list of all sensors

        ('/register', RegistrationHandler),  # first time user connect; this is who I am
        ('/router/post', RouteUserHandler),  # send a new message
    ], debug=True
)
