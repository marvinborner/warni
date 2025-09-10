import time
import os
import ast
from deutschland import nina
from deutschland.nina.api import warnings_api
from pprint import pprint
from notifypy import Notify
from shapely.geometry import shape, Point
from dotenv import load_dotenv

load_dotenv()
SEEN_PATH = str(os.getenv("SEEN_PATH"))
ARS = str(os.getenv("ARS"))
POS = Point(float(os.getenv("LONG")), float(os.getenv("LAT")))
SHOW_ALL = os.getenv("SHOW_ALL") == "True"
INTERVAL = int(os.getenv("INTERVAL"))


class Seen:
    def __init__(self):
        self.needs_sync = False

        if os.path.isfile(SEEN_PATH):
            with open(SEEN_PATH, "r") as f:
                self.seen = ast.literal_eval(f.read())
                print("loaded", self.seen)
        else:
            self.seen = set()

    def sync(self):
        if not self.needs_sync:
            return
        self.needs_sync = False
        with open(SEEN_PATH, "w") as f:
            f.write(str(self.seen))

    def add(self, key):
        self.needs_sync = True
        self.seen.add(key)

    def has(self, key):
        return key in self.seen


def in_geo_range(api, key):
    if SHOW_ALL:
        return True

    geojson = api.get_warning_geo_json(key)
    for feature in geojson["features"]:
        polygon = shape(feature["geometry"])
        if polygon.covers(POS):
            return True
    return False


def add_data(api, seen, data):
    for warning in data:
        key = warning["id"]
        if seen.has(key):
            continue

        seen.add(key)
        if in_geo_range(api, key):
            details = api.get_warning(key)
            handle_warning(warning, details)


def notify_user(title, message):
    notification = Notify()
    notification.title = title
    notification.message = message
    notification.urgency = "critical"
    notification.send()


def handle_warning(warning, details):
    info = details.info[0]  # TODO: are other elements relevant?
    title = "[WARN] " + info.get("headline", "WARNING")
    description = (
        info.get("description", "")
        + "\n\n"
        + info.get("instruction", "no instructions")
    )
    notify_user(title, description)


def check_services():
    try:
        # Biwapp
        data = api.get_biwapp_map_data().value
        add_data(api, seen, data)

        # ARS
        data = api.get_dashboard(ARS).value
        add_data(api, seen, data)

        # DWD
        data = api.get_dwd_map_data().value
        add_data(api, seen, data)

        # Katwarn
        data = api.get_katwarn_map_data().value
        add_data(api, seen, data)

        # LHP
        data = api.get_lhp_map_data().value
        add_data(api, seen, data)

        # Mowas
        data = api.get_mowas_map_data().value
        add_data(api, seen, data)

        # Police
        data = api.get_police_map_data().value
        add_data(api, seen, data)
    except nina.ApiException as e:
        print("Exception: %s\n" % e)


with nina.ApiClient() as api_client:
    api = warnings_api.WarningsApi(api_client)
    seen = Seen()

    while True:
        print("checking...")
        check_services()
        seen.sync()
        time.sleep(60 * INTERVAL)
