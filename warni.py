import ast
import os
import time
import tomli_w
import tomllib
from deutschland import nina
from deutschland.nina.api import warnings_api
from dotenv import load_dotenv
from notifypy import Notify
from platformdirs import user_config_dir
from pprint import pprint
from shapely.geometry import shape, Point

APP_NAME = "warni"
APP_AUTHOR = "borner"

SEEN_PATH = f"/home/{os.getlogin()}/.cache/warni_seen.txt"
ARS = "000000000000"
POS = Point(48.5, 9.0)
SHOW_ALL = False
INTERVAL = 10


def create_config(directory, path):
    print(
        "Not configured yet! Please set the following options. They will be written into your configuration directory (e.g. ~/.config/warni/config.toml)"
    )

    config = {}
    config["seen_path"] = (
        input(f"Warning cache file [{SEEN_PATH}] ").strip() or SEEN_PATH
    )

    print(
        "\nYou can find your ARS here: https://www.xrepository.de/api/xrepository/urn:de:bund:destatis:bevoelkerungsstatistik:schluessel:rs_2025-09-30/download/Regionalschl_ssel_2025-09-30.md"
    )
    config["ars"] = (
        input(f"Amtlicher Regionalschlüssel (ARS) [{ARS}] ").strip() or ARS
    )
    config["long"] = float(input(f"Longitude [{POS.x}] ").strip() or POS.x)
    config["lat"] = float(input(f"Latitude [{POS.y}] ").strip() or POS.y)
    config["show_all"] = (
        input(f"Show all warnings, even outside region [{SHOW_ALL}] ")
        .strip()
        .lower()
        == "true"
        or SHOW_ALL
    )
    config["interval"] = int(
        input(f"Checking interval in minutes [{INTERVAL}] ").strip() or INTERVAL
    )

    config["ars"] = config["ars"][:-7] + "0" * 7

    os.makedirs(directory, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)


def load_config():
    global SEEN_PATH, ARS, POS, SHOW_ALL, INTERVAL

    config_dir = user_config_dir(APP_NAME, APP_AUTHOR)
    config_path = os.path.join(config_dir, "config.toml")

    if not os.path.isfile(config_path):
        create_config(config_dir, config_path)

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

        SEEN_PATH = config["seen_path"]
        ARS = config["ars"]
        POS = Point(config["long"], config["lat"])
        SHOW_ALL = config["show_all"]
        INTERVAL = config["interval"]


class Seen:
    def __init__(self):
        self.needs_sync = False

        if os.path.isfile(SEEN_PATH):
            with open(SEEN_PATH, "r") as f:
                self.seen = ast.literal_eval(f.read())
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
    print(title)
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


# APIs often return 404/etc.
def try_add_data(api, seen, func, *args):
    try:
        data = func(*args).value
        add_data(api, seen, data)
    except Exception as e:
        notify_user("Warni Exception", "Exception: %s\n" % e)


def check_services(api, seen):
    # Biwapp
    try_add_data(api, seen, api.get_biwapp_map_data)

    # ARS
    try_add_data(api, seen, api.get_dashboard, ARS)

    # DWD
    try_add_data(api, seen, api.get_dwd_map_data)

    # Katwarn
    try_add_data(api, seen, api.get_katwarn_map_data)

    # LHP
    try_add_data(api, seen, api.get_lhp_map_data)

    # Mowas
    try_add_data(api, seen, api.get_mowas_map_data)

    # Police
    try_add_data(api, seen, api.get_police_map_data)


def main():
    load_config()
    with nina.ApiClient() as api_client:
        api = warnings_api.WarningsApi(api_client)
        seen = Seen()

        while True:
            print("checking...")
            check_services(api, seen)
            seen.sync()
            time.sleep(60 * INTERVAL)


if __name__ == "__main__":
    main()
