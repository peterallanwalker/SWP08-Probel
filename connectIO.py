# ConnectIO
# For testing SWP08/Probel router control - cross-point switching + label pushing
# Peter Walker, March 2022

import connection_settings as config
import connection
import swp_message

if __name__ == '__main__':
    heading = "SWPO8 Router Control - Cross-point switching and label pushing"
    header_width = len(heading) + 8
    print("\n{}\n -- {} --\n{}".format(header_width * '#', heading, header_width * '-'))

    config = config.get_settings()
