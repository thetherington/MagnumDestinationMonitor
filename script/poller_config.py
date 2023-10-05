import json

from destination_monitor import MagnumDestinationMonitor
from insite_plugin import InsitePlugin


class Plugin(InsitePlugin):
    def can_group(self):
        return False

    def fetch(self, hosts):
        params = {
            "magnum": hosts[-1],
            "client_id": "insite-poller",
            "secret": "secret",
            "tags": ["-ENC-NOC"],
            "nameset": "Global",
        }

        try:
            self.magnum

        except Exception:
            self.magnum = MagnumDestinationMonitor(**params)

        return json.dumps(self.magnum.collect())
