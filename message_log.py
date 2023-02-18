# Class for storing sent & received messages

# manage buffer / max size
# TODO - Manage buffer / limit log size
import datetime
import time


class Logger:
    MAX_TX = 30
    MAX_RX = 100

    def __init__(self):
        self.received = []
        self.sent = []
        self.all = []  # TODO - decide whether to keep sent & recieved separately
                       # (for easy separation into two windows by gui, or keep together for easy print of sequential
                       # messages and have gui separate them... doing both for now

    #def pop_if_full(self, buffer):
    #    if buffer == 'received':
    #        if len(self.received) > MessageLog.MAX_RX:
    #            self.received = self.received[1:]
    #    else:
    #        if len(self.sent) > MessageLog.MAX_TX:
    #            self.sent = self.sent[1:]

    def log(self, timestamp, message, direction):
        if direction == 'sent':
            self.sent.append((timestamp, message))
            #self.pop_if_full('sent')
        else:
            self.received.append((timestamp, message))
            #self.pop_if_full('received')

        self.all.append((timestamp, direction, message))

    def get_message(self, direction):
        if direction == 'sent':
            if self.sent:
                msg = self.sent[0]
                self.sent = self.sent[1:]
                return msg
        else:
            if self.received:
                msg = self.received[0]
                self.received = self.received[1:]
                return msg

    def __str__(self):
        r = ''
        # TODO - provide a function to sort both send and received into a single list ordered by timestamp
        # ... or maybe just hold all messages in one list, with a sent and recieved list (then offload to UI to present in two windows)
        for message in self.all:
            if message[1] == "sent":
                direction = " >>> Sent    : "
            else:
                direction = " <<< Received: "
            #print(message[0])
            #timestamp = datetime.strftime("%a, %d %b %Y %H:%M:%S", datetime.localtime(message[0]))
            if type(message[0]) == datetime.datetime:
                timestamp = message[0].strftime("%a, %d %b %Y %H:%M:%S.%f")[:-3]  #to millisecond
            else:
                timestamp = ''
            #timestamp = message[0]
            r += (timestamp + direction + message[2].__str__() + '\n')
            timestamp = time.time()
            #print("DEBUG TIME", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(timestamp)))
            #print("DEBUG TIME", datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S.%f")[:-3])  #to millisecond
        return r
