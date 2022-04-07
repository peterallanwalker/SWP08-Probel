# Connection Settings handler
# Peter Walker 2020.
# Stripped down from CSCP-MIDI for simple SWP use
# (removed port option as SWP uses fixed port, and removed all the MIDI port handling and control mapping)

import json

import swp_utils

CONFIG_FILE = "connection_settings.json"


# Intended private, for use by this script
def _yes_or_no(string, enter=False, edit=False):
    """
    For parsing cmd line input from user - yes/no prompts
    if string is 'y' or 'yes', case-insensitive, returns 'y'
    if string is 'n' or 'no', case-insensitive, returns 'n'
    else, returns False
    :param string: typically, user input('y/n?')
    :param enter: optional, if enter=True, when string is empty (Enter key alone), returns 'y'
    :param edit: optional, if edit=True, when string is 'e'/'E', return 'n'
    :return: 'y' for affirmative response/acceptance, 'n' for negative response or edit, False for invalid response
    """
    string = string.lower().strip()

    if string in ("y", "yes") or (string == "" and enter):
        return "y"
    elif string in ("n", "no") or (string == "e" and edit):
        return "n"
    else:
        return False


def _validate_ip_address(address):
    """
    Checks if input is a valid IPv4 address
    :param address: string
    :return: True if valid IPv4 address, else False
    """
    address = address.split(".")

    if len(address) != 4:
        return False

    for segment in address:
        try:
            segment = int(segment)
        except ValueError:
            return False

        if segment not in range(256):
            return False

    return True


def _load_settings():
    """
    Check if configuration file exists
    :return: Dict of settings (returns defaults if none saved)
    """
    try:
        with open(CONFIG_FILE, "r") as config:
            r = json.load(config)

    except FileNotFoundError:
        print("'{}' file not found. Enter a few details to get started...".format(CONFIG_FILE))
        r = False

    except json.decoder.JSONDecodeError:
        print("'{}' file is invalid. Enter a few details to get started...".format(CONFIG_FILE))
        r = False

    if not r:
        r = {"Router IP Address": None,
             "Port": 61000,
             "Protocol": "swp08",
             "label length": 4
             }
    return r


def _ask_ip_address():
    """
    Asks user to input an IP address
    Checks input is a valid IP address, keeps asking until it is
    :return: string - user inputted IP address
    """
    valid = False
    while not valid:
        ip_address = input("Enter mixer's IP address: ")
        if _validate_ip_address(ip_address):
            return ip_address


def _ask_label_length():
    options = ""
    for option in swp_utils.CHAR_LEN_CODES.keys():
        options += (str(option) + " ")
    valid = False
    while not valid:
        # TODO - format output to print keys
        # TODO - this is changing the json file, but does not seem to be changing the label len displayed
        label_length = input("Enter SWP label length, options: {}: ".format(options))
        if not label_length.isnumeric():
            continue
        elif int(label_length) in swp_utils.CHAR_LEN_CODES:
            return int(label_length)


def _confirm_settings(config):
    """
    Ask user if they want to keep the last used settings or enter new ones
    :return: Dict of user confirmed settings
    """
    use_settings = False

    # Present last used settings and ask to confirm or update
    while not use_settings:
        print("Last used connection settings: ")
        for heading in config:
            print("\t", heading, ":", config[heading])

        use_settings = _yes_or_no(input("\nUse these settings? (y/n): "), enter=True)

    if use_settings == "n":
        # User does not want to keep last used settings, so get their input for new settings
        config["Router IP Address"] = _ask_ip_address()
        if config["Protocol"] == "SWP08":
            config["Label Length"] = _ask_label_length()
    return config


# intended public, for use from outside of this script
def get_settings():
    """
    Loads connection settings (just IP address in this version) & gets user to confirm or edit
    :return: dict of user confirmed settings
    """
    # TODO - handle corrupt/malformed json settings file
    r = _load_settings()
    r = _confirm_settings(r)
    return r


def save_settings(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


if __name__ == '__main__':

    heading = "SWPO8 connection settings"
    header_width = len(heading) + 8
    print("\n{}\n -- {} --\n{}".format(header_width * '#', heading, header_width * '-'))

    settings = get_settings()
    save_settings(settings)

    for setting in settings:
        print(setting, ":", settings[setting])