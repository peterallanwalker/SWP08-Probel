# SWP08/Probel - ConnectIO

A Python3 application for testing router control - Source to destination cross-point switching and pushing of labels 
using the [SWP08/Probel protocol](https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf)
(Other versions of the protocol doc are available in [this repo's protocol docs folder](https://github.com/peterallanwalker/SWP08-Probel/tree/master/protocol%20docs))

#### Downloads:
- Stable/tested: [Download ConnectIO CLI V1.2](https://github.com/peterallanwalker/SWP08-Probel/archive/refs/heads/ConnectIO_CLI_V1.2.zip)
- Beta: [Download ConnectIO CLI V1.3](https://github.com/peterallanwalker/SWP08-Probel/archive/refs/heads/ConnectIO_CLI_V1.3.zip)
- Proto GUI: in progress

Cross-point switching tested with Calrec Brio and Apollo+/Impulse audio mixers.
Label pushing tested with Calrec Apollo+ (label exchange is not supported on Brio or Summa)

To help with debugging if needed, telnet into the Calrec router on port 55555 
(default address of Impulse router on the internal network via interface 2 is 172.16.255.10), 
and enter `audit/update 105` & `audit/update 70` to enable SWP related debug output from the Calrec router. 
(Note router telnet session may not be responsive to commands initially, in which case, 
repeatedly entering `help` until the help info is displayed gets it recognising input)


## connectIO.py
The main script, providing CLI based user interaction for exchanging SWP08 messages with a router. 

Currently supports making connections with optional label to push, and requesting current connection state (tally dump). 

Note CLI values are protocol level / zero-based, whereas Calrec UI & CSV is one-based, so a matrix/level/id of e.g. 1 
in the UI/CSV is 0 in the CLI.


### Supporting files

#### client_connection.py
Client-side IP socket connection manager. Provides the Connection class which runs a separate thread buffering 
incoming messages, and provides public methods for sending messages and getting received messages from the input buffer

Connection.send() accepts raw byte strings or swp_message objects. Connection.get_message returns the oldest message in the input buffer (along with the timestamp of when it was received) 

#### swp_message.py
Provides classes for various SWP08 message types. Message objects provide an `encoded` attribute which is a byte string
that can be passed to a socket, e.g. `client_connection.Connection.send()`, and a `__str__` method, so they print informatively. 

Also provides a `decode()` function that takes byte-strings (as received over a socket via swp_unpack) and returns
swp message objects.

#### swp_unpack.py
Checks byte strings for SWP08 headers/SOM and end-of-message/EOM, returning a list of separated messages. 
Handles potential case of a message being split between separate socket receive data chunks.

#### swp_utils.py
Provides constants and utility functions for working with the SWP08 protocol

#### connection_settings.py
Handles loading of last used settings, user confirm/edit and save as json.

#### router_emulator.py
Basic SWP08 router emulator with server side socket for testing connectIO locally in the absence of a real router.
Usage: start router_emulator.py, then start connectIO.py in another terminal window and enter address 127.0.0.1 
(localhost) for to connect with the router emulator. The emulator requires a source & destination list provided in 
the Calrec csv export format, located within the same folder (multiple csv files can be kept, with user prompted to choose
one at start up)

#### import_io.py
Used by router emulator (& ConnectIO GUI) to import Calrec VPB config CSV files.

#### socket_connection_manager.py
Provides server-side equivalent of client_connection.py for use by router_emulator.py

### TODO:
- [ ] Handle DLE's within payload properly... escape them when encoding payload. 
  Decode was failing, e.g. connect destination 17 to source 4, gets encoded as \x10\x03 which 
  I'm identifying as a false EOM but am not parsing to find the actual EOM in such case!

- [ ] Set a delay - Brio seems to have a small lag after ACK before sending tally dump (check timestamps in sample output) 
  maybe around generic send / connectIO line 97... looks like I need to add 500ms 
  (currently, user needs to press Enter to view remaining messages in receive buffer to see them before moving on).
  
- [ ] Add the mute ID as a user option. Currently, silence/mute/no-connection is hard-coded with the ID 1023 (1024 in UI/csv). Note, Impulse seems to return source ID 0   if there is no source patched, (at least if no silence source id set in COnfigure). Brio does not return a tally if no source.

- [ ] Change message str methods to return 1 based output to match Calrec UI/csv

- [ ] Setup default node creation for router emulator so can run without a csv

- [ ] Fix/check GUI issues
- [ ] Add port as a settings parameter
