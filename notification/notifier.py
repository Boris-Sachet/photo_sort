from config import Config
from notification.pushbullet import PushbulletNotify
from notification.pushover import PushoverNotify


class Notifier:
    def __init__(self):
        self.notifiers = []
        if Config.pushbullet_api_key:
            self.notifiers.append(PushbulletNotify())
        if Config.pushover_token:
            self.notifiers.append(PushoverNotify())

    def notify(self, title, message):
        for notifier in self.notifiers:
            notifier.notify(title, message)
