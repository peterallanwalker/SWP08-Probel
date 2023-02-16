# Settings handler for ConnectIO GUI
# Peter Walker 2022.
# Adapted from cli based settings_cli.py

import json
import swp_utils

CONFIG_FILE = "connectIO_gui_settings.json"


def validate_ip_address(address):
    """
    Checks if input is a valid IPv4 address
    :param address: string
    :return: True if valid IPv4 address, else False
    """
    address = address.split(".")

    if len(address) != 4:
        return False

    for segment in address:
        if not segment.isnumeric():
            return False
        if int(segment) not in range(255):
            return False

    return True


def load_settings():
    """
    Check if configuration file exists
    :return: Dict of settings (returns defaults if none saved)
    """
    try:
        with open(CONFIG_FILE, "r") as config:
            r = json.load(config)

    except FileNotFoundError:
        print("'{}' file not found".format(CONFIG_FILE))
        r = False

    except json.decoder.JSONDecodeError:
        print("'{}' file is invalid, creating default".format(CONFIG_FILE))
        r = False

    if not r:
        r = {"Router Name": '',
             "Router IP Address": '',
             "Port": 61000,
             "Protocol": "SWP08",
             "Label Length": 12,
             "IO Config File": ''
             }
    return r


def save_settings(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


if __name__ == '__main__':

    settings = load_settings()

    for setting in settings:
        print(setting, ":", settings[setting])