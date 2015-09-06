import json
import logging
import urllib2

from odb.sensor_data import SensorData

__author__ = 'drathier'


def maps(places):
    url = "https://maps.googleapis.com/maps/api/directions/json?origin={0}&destination={1}&waypoints=optimize:true|{2}&key=AIzaSyCDS-Ejka2KbVFP34MHYScz3Z9oWqxlQWc".format(
        places[0], places[-1], "|".join(places[1:-1]))
    res = ""
    try:
        res = urllib2.urlopen(url).read()
        res = json.loads(res)
    except:
        pass

    logging.info("maps got {0}".format(places))
    logging.info("maps {0}".format(res))
    logging.info("url {0}".format(url))

    return res


def tsp(curr_loc):
    res = SensorData.all_newest_both()

    res = sorted(res, key=lambda a: a[1].estValue(a[0]))

    res = res[:8]

    logging.info(res)

    points = [curr_loc] + ["{0},{1}".format(w[0].wgs84.lat, w[0].wgs84.lon) for w in res] + [curr_loc]

    route = maps(points)

    logging.info("route {0}".format(route))

    order = route['routes'][0]['waypoint_order']
    waypoints = route['geocoded_waypoints']

    ans = [curr_loc]
    wps = []
    for o in order:
        ans.append(points[1:-1][o])
        wps.append(waypoints[o])

    logging.info("ans {0}".format(ans))

    return ans, waypoints
