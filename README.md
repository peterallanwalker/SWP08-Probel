# SWP08/Probel - ConnectIO CLI, V1.2

A Python3 application for testing router control - Source to destination cross-point switching and pushing of labels 
using the [SWP08/Probel protocol](https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf)
(Other versions of the protocol doc are available in [this repo's protocol docs folder](https://github.com/peterallanwalker/SWP08-Probel/tree/master/protocol%20docs))

#### [Download ConnectIO CLI V1.2](https://github.com/peterallanwalker/SWP08-Probel/archive/refs/heads/ConnectIO_CLI_V1.2.zip)

Cross-point switching tested with Calrec Brio and Apollo+/Impulse audio mixers.
Label pushing tested with Calrec Apollo+ (label exchange is not supported on Brio or Summa)

To help with debugging if needed, telnet into the Calrec router on port 55555 
(default address of Impulse router on the internal network via interface 2 is 172.16.255.10), 
and enter `audit/update 105` & `audit/update 70` to enable SWP related debug output from the Calrec router. 
(Note router telnet session may not be responsive to commands initially, in which case, 
repeatedly entering `help` until the help info is displayed gets it recognising input)

## connectIO.py
The main script, providing CLI based user interaction for exchanging SWP08 messages with a router. 

### Supporting files

#### client_connection.py
Client-side IP socket connection manager. Provides the Connection class which runs a separate thread buffering 
incoming messages, and provides public methods for sending messages and getting received messages from the input buffer

Connection.send() accepts raw byte strings or swp_message objects. Connection.get_message returns the oldest message in the input buffer (along with the timestamp of when it was received) 

#### swp_message.py
Provides classes for various SWP08 message types that accept human parameters, and a `decode()` method that parses
bytes and returns message classes.

### swp_unpack.py
Checks byte strings for SWP08 headers/SOM and end-of-message/EOM, returning a list of separated messages. 
Handles potential case of a message being split between separate socket receive data chunks.

### swp_utils.py
Provides constants and utility functions for working with the SWP08 protocol

### connection_settings.py
Handles loading of last used settings, user confirm/edit and save as json.

#### router_emulator.py
Basic SWP08 router emulator with server side socket for testing ConnectIO locally in the absence of a real router

#### import_io.py
Used by router emulator (& ConnectIO GUI) to import Calrec VPB config CSV files.

#### socket_connection_manager.py
Provides server-side equivalent of client_connection.py for use by router_emulator.py

### TODO:
- [ ] Check handling of DLE's within payload properly... check I'm properly escaping them when encoding payload. 
  Decode was failing, e.g. connect destination 16 to source 3, gets encoded as \x16\x03 which 
  I'm identifying as a false EOM but am not parsing to find the actual EOM in such case!... Possibly fixed, can't remember!

 
