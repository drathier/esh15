from google.appengine.ext import ndb

__author__ = 'drathier'


class User(ndb.Model):
    userid = ndb.StringProperty(required=True)
    ch_token = ndb.StringProperty()
    emails = ndb.StringProperty(repeated=True)

    def _pre_put_hook(self):
        # self.id = "user_id:" + self.userid
        self.key = ndb.Key(User, "user_id:" + self.userid)
