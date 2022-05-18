# - CSS/QSS constants
# - Peter Walker, May 2022
#
# - example usage:
# - widget.setStyleSheet(CSS['<class name>']

# - Color palette from:
# - https://www.sketchappsources.com/free-source/1049-flat-ui-color-pallete-sketch-freebie-resource.html
COLOR_PALETTE = {"clouds": "#ecf0f1",
                 "silver": "#bdc3c7",
                 "concrete": "#95a5a6",
                 "dark green": "#27ae60",
                 "dark red": "#c0392b",
                 }

# - Background & text colours for state indication (for use in status bar depending on connection state)
CLASSES = {"good": "background-color:#0a0; color:#fff;",
           "warning": "background-color:#FF8C00; color:white;",
           "error": "background-color:#a00; color:white;",
           }

CSS = {"message even": "background-color: {}; border: None;".format(COLOR_PALETTE['clouds']),
       "message odd": "background-color: {};".format(COLOR_PALETTE['silver']),
       "ACK": CLASSES["good"],
       "NAK": CLASSES["error"],
       "Starting": CLASSES["good"],
       "Connected": CLASSES["good"],
       "Connection Lost!": CLASSES["error"],
       "Not Connected": CLASSES["error"],

       }
