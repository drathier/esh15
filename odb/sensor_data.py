from datetime import datetime
import logging
import math

from google.appengine.ext import ndb

from odb.sensor import Sensor

__author__ = 'drathier'


class SensorData(ndb.Model):
    sensor_id = ndb.StringProperty(required=True)
    raw = ndb.StringProperty(required=True)
    added = ndb.DateTimeProperty(auto_now_add=True)
    lastmod = ndb.DateTimeProperty(auto_now=True)
    value = ndb.FloatProperty(required=True)

    def _pre_put_hook(self):
        sensor = Sensor.query(Sensor.sensor_id == self.sensor_id).fetch(1)
        if not sensor:
            sensor = Sensor(sensor_id=self.sensor_id)
            sensor.put()
        else:
            sensor = sensor[0]

        # calculate real value
        if sensor.type == Sensor.DISTANCE:
            v = float(self.raw) / 4096 * 2 * 1.4
            self.value = 76.35 * (math.e ** (-3.469 * v)) + 17.3 * (math.e ** (-0.5599 * v))

    @classmethod
    def all_by_hours(cls, sensor_id):
        sensor = Sensor.query(Sensor.sensor_id == sensor_id).fetch(1)[0]
        hours = []
        pair = []
        for hour in sensor.hours:
            if not pair:
                pair += [hour]
            else:
                hours += pair
                pair = []

        return SensorData.query(*[start < SensorData.lastmod < stop for start, stop in hours])

    @classmethod
    def last_n_by_hours(cls, sid, limit=None):
        sensor = Sensor.query(Sensor.sensor_id == sid).fetch(1)[0]
        if not sensor.hours:
            return cls.last_n(sid, limit)
        hours = []
        pair = []
        for hour in sensor.hours:
            logging.info("pair {0}; hours {1}".format(pair, hours))
            if not pair:
                pair += [hour]
            else:
                hours += pair
            pair = []

            return SensorData.query(Sensor.sensor_id == sid,
                                    *[start < SensorData.lastmod < stop for start, stop in hours])

    @classmethod
    def last_n(cls, sid, limit=None):
        return SensorData.query(SensorData.sensor_id == sid).order(-SensorData.added).fetch(limit)

    @classmethod
    def all_newest(cls):
        ids = [s.sensor_id for s in Sensor.all()]
        return [SensorData.query(SensorData.sensor_id == i).order(-SensorData.added).fetch(1)[0] for i in ids]

    def color(self):
        sensor = Sensor.query(Sensor.sensor_id == self.sensor_id).fetch(1)[0]
        if sensor.type == Sensor.DISTANCE:
            if self.value > 25:
                return 'red'
            elif self.value > 15:
                return 'orange'
            elif self.value > 10:
                return 'gold'
            else:
                return 'green'

    def sensor(self):
        return Sensor.query(Sensor.sensor_id == self.sensor_id).fetch(1)[0]

    def json(self):
        d = self.to_dict()
        d["added"] = datetime.isoformat(d["added"], 'T')
        d["lastmod"] = datetime.isoformat(d["lastmod"], 'T')
        return d
