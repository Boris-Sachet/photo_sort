from pushbullet import Pushbullet

from config import Config

class PushbulletNotify:
    def __init__(self):
        self.conn = Pushbullet(Config.pushbullet_api_key, Config.pushbullet_encryption_key)

    def notify(self, title, message):
        self.conn.push_note(title, message)
