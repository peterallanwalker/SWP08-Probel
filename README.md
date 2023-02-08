# SWP08/Probel

[Download ConnectIO CLI V1.2](https://github.com/peterallanwalker/SWP08-Probel/archive/refs/heads/ConnectIO_CLI_V1.2.zip)

ConnectIO GUI - crosspoint matrix with label handling is beta

### Router control using the [SWP08/Probel protocol](https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf)
(Other versions of the protocol doc are available in [this repo's protocol docs folder](https://github.com/peterallanwalker/SWP08-Probel/tree/master/protocol%20docs))

## Source to destination cross-point switching and pushing of labels.

Cross-point switching tested with Calrec Brio and Apollo+/Impulse audio mixers.
Label pushing tested with Calrec Apollo+ (label exchange is not supported on Brio or Summa)

To help with debugging if needed, telnet into the Calrec router on port 55555 (default address of Impulse router on the internal network via interface 2 is 172.16.255.10), and enter `audit/update 105` & `audit/update 70` to enable SWP related debug output. (Note router telnet session may not be responsive to commands initially, in which case, repeatedly entering `help` untill the help info is displayed gets it recognising input)

#### TODO:
- [ ] Handle DLE's within payload properly... check I'm properly escaping them when encoding payload. Decode is failing, 
e.g. connect destination 16 to source 3, gets encoded as \x16\x03 which I'm identifying as a false EOM but am not parsing
  to find the actual EOM in such case!

## Project Files

### connectIO.py
A main entry point to the application for users - creates a connection (based on last used settings if any, prompts for confrim/edit), prompts for individual source-to-destination routes with optional label to pass.


### swp_message.py
Provides classes to represent various SWP08 command messages. All messages classes provide an `encoded` attribute which 
is the byte string as sent/received by the socket connection

`Connect` - Connect message (swp protocol command 2) to send to a router, 
and can be instantiated either with node objects; `Connect(source Node, destination Node)`,
or with integer IDs and named matrix & level; `Connect(source id, destination id, matrix=n, level=n)`.


`Connected` - Connected message (swp protocol command 4), as sent by a router when it makes connections.
This class inherits from `Connect` and can also be instantiated using either Node objects or integers. 

`GetConnections` - Cross-point tall dump request message (swp protocol 21), 




`Message.push_labels(labels, first_destination)` takes a list of labels (of any character length), and a single integer ID of the first destination. If 
multiple labels are provided, the receiving device (Calrec Apollo+/Artemis+ audio mixer) will apply them to consecutive IDs. char_len is an optional argument, defaulting to 4. SWP supports 4, 8, 12, 16 or 32 character length labels (this sets what is displayed on the mixer, but the function accepts labels of any length, truncating long ones and padding short ones with spaces).... In my tests with Apollo+ it will display 4, 8 or 12 char labels. If you send 16 or 32 character label messages, the mixer will update but only display the first four chars. (SWP08 message 107).

`Message.push_labels_extended(labels, first_destination)` same as `Message.push_labels` but supports a greater number of IDs (? I think - not fully tested). (SWP08 message 235)

`Message.decode(message byte string)` takes a (pre-validated) SWP message as a byte string and creates a message object if the command type is supported. Currently supported messages for decoding are "connect"(SWP08 message 2) and "connected"(SWP08 message 4 - sent from the mixer in response to a Connect message, or if connections with SWP08 IDs are changed by other means such as Calrec/Mixer UI).

The `Message` class provides a `__str__` method so info can be printed to view the parameters of the a message object using `print(message)`.

`message.encoded` is a byte string of the encoded message that can be sent to a mixer/router (Using the Connection class's `connection.send` method).

##### TODO
- [ ] Test different char length labels.
- [ ] Provide support for non-zero matrix & level
- [ ] Test IDs multiplier support for IDs > 255 up to 1024 
- [ ] Support more messages types
- [ ] Sort either the init or the \__str__ so I don't need to populate all values for all message types (think I default init values to None instead of False or other for a reason but can't remember why offhand

### connection.py
Provides the Connection class `Connection(IP_address, port, protocol=protocol)` to handle an IP socket connection between the application and the mixer/router. IP_address is a string, port is an int, protocol is an optional string - "CSCP" or "SWP08" currently supported, default is CSCP (so pass "SWP08" when instantiating for router control). The instantiated connection object runs a separate thread for receiving and buffering incoming messages without blocking the main application. Provides `Connection.send_message()` & `Connection.get_message()` methods to send (`connection.send(message.encoded)`) and receive messages (`message = connection.receive()` 'pops' off the oldest received message in the buffer - `connection._messages[0]`, so the next call to `receive()` returns the next message). 

Note, incoming bytes are parsed into separate validated SWP/CSCP messages based on header/SOM, (checksum not currently validated for SWP messages) and end-of-message/EOM by swp_unpack before being added to the receive() buffer.

#### TODO
- [ ] Calrec router seems to be dropping the SWP connection at times - check the ping in connection.run, its supposed to prompt for activity when quiet and attempt reconnect if no response (... will need a "benign" swp message that elicits a response without making a state change).
- [ ] Might be handy to provide receive_buffer_len() and flush_buffer() methods if I feel the need to externally call `len(connection._messages)` or `connection._messages = []` (not needing this outside of early CSCP debug so far, but not currently displaying messages responses nicely inline with the main connectIO.py output so may be handy for that).
- [ ] Change user input to be 1 based / match the values set in calrec UI and CSV? (and match in message print output)

### swp_utils.py
Provides constants for the SWP08 protocol and a calculate_checksum() function.

### swp_unpack.py
Checks byte strings for SWP08 headers/SOM and end-of-message/EOM, returning a list of separated messages. Handles potential case of a message being split between separate socket receive data chunks.

### connection_settings.py
Handles loading of last used settings, user confirm/edit and save as json.

### prot0x.py
Rough testing/in-progress dev scripts.



 
