# ConnectIO
# For testing SWP08/Probel router control - cross-point switching + label pushing
# Peter Walker, March 2022

import connection_settings as config
from connection import Connection
import swp_message

if __name__ == '__main__':
    # - Format & print header
    heading = "SWPO8 Router Control - Cross-point switching and label pushing"
    header_width = len(heading) + 8
    print("\n{}\n -- {} --\n{}".format(header_width * '#', heading, header_width * '-'))

    # - Get last used IP address, and prompt user accept/change
    settings = config.get_settings()
    # - Save user confirmed settings for next time
    config.save_settings(settings)

    # - Open a TCP connection with the router
    connection = Connection(settings["Router IP Address"], settings["Port"], settings["Protocol"])

    # - Wait for connection status to be Connected
    print("Waiting for connection...")
    update_freq = 10000000
    count = 0
    while connection.status != "Connected":
        count += 1
        if count % update_freq == 0:
            print("Waiting...", connection.status)
            pass

    print(connection.status)

    command = input("Enter source, de")
    source, destination, label = input()