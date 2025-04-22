from config import Config
from notification.pushover import PushoverNotify

Config.init()
notif = PushoverNotify()
result = notif.notify("test title", "test message")
print(result)
