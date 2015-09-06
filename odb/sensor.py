from datetime import datetime
from google.appengine.ext import ndb

__author__ = 'drathier'


class Sensor(ndb.Model):
    DISTANCE = 'distance'

    sensor_id = ndb.StringProperty(required=True)
    wgs84 = ndb.GeoPtProperty()
    name = ndb.StringProperty()
    type = ndb.StringProperty()  # choices=["distance", "ir", "hall", "test"])  # only using distance for now

    hours = ndb.TimeProperty(repeated=True)  # first, third, fifth etc. are opening hours

    @classmethod
    def all(cls):
        return Sensor.query().order(Sensor.sensor_id).fetch()

    def json(self):
        d = self.to_dict()
        if 'wgs84' in d and d['wgs84']:
            d['wgs84'] = "{0}, {1}".format(self.wgs84.lon, self.wgs84.lat)
        d["url"] = "/sensor?sid={0}".format(self.sensor_id)
        d["chart_url"] = "/chart?sensor={0}".format(self.sensor_id)

        d["hours"] = ["{0}:{1}".format(x.hour, x.minute) for x in d["hours"]]
        return d

    @classmethod
    def by_id(cls, id):
        return Sensor.query(Sensor.sensor_id == id).fetch(1)[0]
