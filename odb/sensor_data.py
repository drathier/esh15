from datetime import datetime, time, timedelta
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
            v = float(self.raw) / 4096 * 3 * 1.4
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
    def last_n_by_hours(cls, sid, limit=None, check_hours=True):
        sensor = Sensor.query(Sensor.sensor_id == sid).fetch(1)[0]
        if not sensor.hours:
            return cls.last_n(sid, limit)
        hours = []
        pair = []
        for hour in sensor.hours:
            logging.info("pair {0}; hours {1}".format(pair, check_hours))
            pair += [hour]
            if len(pair) > 1:
                hours += [pair]
                pair = []

        logging.info("done; pair {0}; hours {1}".format(pair, check_hours))
        logging.info(sensor.hours)

        def ok_hour(sd):
            if not check_hours:
                return True
            x = sd.added
            t = time(x.hour, x.minute)
            for start, stop in hours:
                if start < t < stop:
                    logging.info("{0} < {1} < {2}; {3}".format(start, t, stop, sd))
                    return True
            logging.info("NOT INSIDE {0}; {1}".format(t, sd))
            return False

        sdata = filter(ok_hour, SensorData.query(Sensor.sensor_id == sid).order(-SensorData.added).fetch())

        def dt_between(start, stop, time):
            logging.info("dt_between(start={0}, stop={1}, time={2})".format(start, stop, time))
            ret = []
            s = start
            logging.info("pre; {0} < {1}".format(s, stop))
            while s < stop:
                logging.info("{0} < {1}".format(s, stop))
                r = s
                r = r.replace(hour=time.hour, minute=time.minute, second=0, microsecond=1)
                ret += [r]
                s += timedelta(days=1)
            return ret

        if check_hours:
            start, stop = sdata[-1].added, sdata[0].added

            for pair in hours:
                logging.info("pair in hours; {0}; {1}".format(pair, hours))
                logging.info("dt_between; {0}".format(dt_between(start, stop, pair[0])))

                for t in zip(dt_between(start, stop, pair[0]), dt_between(start, stop, pair[1])):
                    logging.info("zip {0}".format(t))
                    if t:
                        # add null values to make gaps in the graph
                        s1 = SensorData()
                        s1.added = t[0] + timedelta(seconds=1)
                        s1.lastmod = s1.added
                        s1.sensor_id = sdata[0].sensor_id
                        s2 = SensorData()
                        s2.added = t[1] - timedelta(seconds=1)
                        s2.lastmod = s2.added
                        s2.sensor_id = sdata[0].sensor_id
                        logging.info("adding zeroed SensorData {0}; {1}".format(s1, s2))
                        sdata += [s1, s2]

            sdata = sorted(sdata, key=lambda a: a.added, reverse=True)

        return sdata

        return SensorData.query(Sensor.sensor_id == sid,
                                ndb.OR(
                                    *[ndb.AND(start < SensorData.lastmod, SensorData.lastmod < stop)
                                      for start, stop in hours]))

    @classmethod
    def last_n(cls, sid, limit=None):
        return SensorData.query(SensorData.sensor_id == sid).order(-SensorData.added).fetch(limit)

    @classmethod
    def all_newest(cls):
        ids = [s.sensor_id for s in Sensor.all()]
        return [SensorData.query(SensorData.sensor_id == i).order(-SensorData.added).fetch(1)[0] for i in ids]

    @classmethod
    def all_newest_both(cls):
        ids = Sensor.all()
        return [(i, SensorData.query(SensorData.sensor_id == i.sensor_id).order(-SensorData.added).fetch(1)[0]) for i in
                ids]

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
