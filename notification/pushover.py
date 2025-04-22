import http.client, urllib

from config import Config


class PushoverNotify:
    def __init__(self):
        self.url = "api.pushover.net:443"
        self.token = Config.pushover_token
        self.user = Config.pushover_user
        self.conn = http.client.HTTPSConnection(self.url)

    def notify(self, title, message):
        self.conn.request("POST", "/1/messages.json",
            urllib.parse.urlencode({
                "token": self.token,
                "user": self.user,
                "title": title,
                "message": message,
            }), {"Content-type": "application/x-www-form-urlencoded"})
        return self.conn.getresponse()
