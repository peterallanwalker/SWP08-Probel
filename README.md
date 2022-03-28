# SWP08/Probel
### Router control using the [SWP08/Probel protocol](https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf)
(Other versions of the protocol doc are available in [this repo's protocol docs folder](https://github.com/peterallanwalker/SWP08-Probel/tree/master/protocol%20docs))

## Source to destination cross-point switching and pushing of labels.

Cross-point switching tested with Calrec Brio and Apollo+/Impulse audio mixers.
Label pushing tested with Calrec Apollo+ (label exchange is not supported on Brio or Summa)

To help with debugging, telnet into the Calrec router on port 55555 (default address of Impulse router on the internal network via interface 2 is 172.16.255.10), and enter `audit/update 105` & `audit/update 70` to enable SWP related debug output. (Note router telnet session may not be responsive to commands initially, in which case, repeatedly entering `help` untill the help info is displayed gets it recognising input)

## Project Files

### connectIO.py
