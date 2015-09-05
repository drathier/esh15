from google.appengine.ext import ndb

__author__ = 'drathier'


class Sensor(ndb.Model):
    DISTANCE = 'distance'

    sensor_id = ndb.StringProperty(required=True)
    wgs84 = ndb.GeoPtProperty()
    name = ndb.StringProperty()
    type = ndb.StringProperty()  # choices=["distance", "ir", "hall", "test"])  # only using distance for now

    @classmethod
    def all(cls):
        return Sensor.query().order(Sensor.sensor_id).fetch()

    def json(self):
        d = self.to_dict()
        if 'wgs84' in d and d['wgs84']:
            d['wgs84'] = "{0}, {1}".format(self.wgs84.lat, self.wgs84.lon)
        d["url"] = "/sensor?sid={0}".format(self.sensor_id)
        return d
