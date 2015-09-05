from datetime import datetime
import math

from google.appengine.ext import ndb

from odb.sensor import Sensor

__author__ = 'drathier'


class SensorData(ndb.Model):
    sensor_id = ndb.StringProperty(required=True)
    raw = ndb.StringProperty(required=True)
    added = ndb.DateTimeProperty(auto_now_add=True)
    lastmod = ndb.DateTimeProperty(auto_now=True)
    value = ndb.FloatProperty()

    def _pre_put_hook(self):
        sensor = Sensor.query(Sensor.sensor_id == self.sensor_id).fetch(1)
        if not sensor:
            sensor = Sensor(sensor_id=self.sensor_id)
            sensor.put()
        else:
            sensor = sensor[0]

        # calculate real value
        if sensor.type == Sensor.DISTANCE:
            v = float(self.raw)
            self.value = 76.35 * math.e ** -3.469 * v + 17.3 * math.e ** -0.5599 * v

    @classmethod
    def last_n(cls, sid, limit=None):
        return SensorData.query(SensorData.sensor_id == sid).order(SensorData.added).fetch(limit)

    def json(self):
        d = self.to_dict()
        d["added"] = datetime.isoformat(d["added"], 'T')
        d["lastmod"] = datetime.isoformat(d["lastmod"], 'T')
        return d
